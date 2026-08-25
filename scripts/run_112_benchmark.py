from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Sequence


RUN_ID_PATTERN = re.compile(r"^\d{8}T\d{6}Z(?:-[A-Za-z0-9._-]+)?$")


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def format_utc(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def default_run_id() -> str:
    return utc_now().strftime("%Y%m%dT%H%M%SZ")


def resolve_path(path: Path, repo_root: Path) -> Path:
    return path if path.is_absolute() else (repo_root / path).resolve()


def load_dataset(dataset_dir: Path, expected_count: int | None = 112) -> list[dict[str, Any]]:
    if not dataset_dir.is_dir():
        raise FileNotFoundError(f"Dataset directory does not exist: {dataset_dir}")

    records: list[dict[str, Any]] = []
    seen_indices: set[int] = set()

    for path in dataset_dir.glob("*.json"):
        try:
            item = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON in {path}: {exc}") from exc

        if not isinstance(item, dict):
            raise ValueError(f"Dataset item must be an object: {path}")

        idx = item.get("idx")
        problem = item.get("problem")

        if not isinstance(idx, int):
            raise ValueError(f"Dataset item idx must be an integer: {path}")
        if idx in seen_indices:
            raise ValueError(f"Duplicate dataset idx={idx}: {path}")
        if not isinstance(problem, str) or not problem.strip():
            raise ValueError(f"Dataset item problem must be a non-empty string: {path}")

        seen_indices.add(idx)
        records.append(item)

    records.sort(key=lambda item: item["idx"])

    if expected_count is not None and len(records) != expected_count:
        raise ValueError(
            f"Expected {expected_count} dataset items, found {len(records)} in {dataset_dir}"
        )

    return records


def write_agent_input(records: Sequence[dict[str, Any]], input_file: Path) -> None:
    """Write only idx/problem so reference answers cannot reach ReasoningAgent."""
    input_file.parent.mkdir(parents=True, exist_ok=True)
    with input_file.open("w", encoding="utf-8") as file:
        for item in records:
            safe_item = {
                "idx": item["idx"],
                "problem": item["problem"],
            }
            file.write(json.dumps(safe_item, ensure_ascii=False) + "\n")


def dataset_digest(records: Iterable[dict[str, Any]]) -> str:
    digest = hashlib.sha256()
    for item in records:
        payload = json.dumps(
            item,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        digest.update(payload)
        digest.update(b"\n")
    return digest.hexdigest()


def read_json_object(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {
            "status": "unreadable",
            "error": {
                "type": type(exc).__name__,
                "message": str(exc),
            },
        }
    return value if isinstance(value, dict) else {"status": "invalid_record"}


def build_summary(
    records: Sequence[dict[str, Any]],
    output_dir: Path,
    *,
    run_id: str,
    runner_exit_code: int,
) -> dict[str, Any]:
    per_item: list[dict[str, Any]] = []
    status_counts: Counter[str] = Counter()
    subject_counts: Counter[str] = Counter(
        str(item.get("subject") or "unknown") for item in records
    )

    for item in records:
        idx = item["idx"]
        result_path = output_dir / f"{idx}.json"

        if not result_path.exists():
            status = "missing"
            result: dict[str, Any] = {}
        else:
            result = read_json_object(result_path)
            status = str(result.get("status") or "unknown")

        final_response = result.get("final_response", "")
        trace = result.get("trace", [])
        error = result.get("error", {})

        response_chars = len(final_response) if isinstance(final_response, str) else 0
        trace_steps = len(trace) if isinstance(trace, list) else 0
        error_type = error.get("type") if isinstance(error, dict) else None

        status_counts[status] += 1
        per_item.append(
            {
                "idx": idx,
                "subject": str(item.get("subject") or "unknown"),
                "status": status,
                "response_chars": response_chars,
                "trace_steps": trace_steps,
                "error_type": error_type,
                "output_file": f"{idx}.json",
            }
        )

    total = len(records)
    success_count = status_counts.get("success", 0)

    return {
        "run_id": run_id,
        "total": total,
        "runner_exit_code": runner_exit_code,
        "counts": {
            "success": success_count,
            "error": status_counts.get("error", 0),
            "missing": status_counts.get("missing", 0),
            "other": total
            - success_count
            - status_counts.get("error", 0)
            - status_counts.get("missing", 0),
        },
        "success_rate": success_count / total if total else 0.0,
        "subjects": dict(sorted(subject_counts.items())),
        "warning": (
            "This summary checks execution completeness only; "
            "it is not the official mathematical judge."
        ),
        "records": per_item,
    }


def get_repository_commit(repo_root: Path) -> str | None:
    try:
        completed = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repo_root,
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        completed = None

    if completed is not None:
        value = completed.stdout.strip()
        if value:
            return value

    github_sha = os.environ.get("GITHUB_SHA")
    return github_sha or None


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def run_benchmark(args: argparse.Namespace) -> int:
    repo_root = Path(__file__).resolve().parents[1]
    dataset_dir = resolve_path(args.dataset_dir, repo_root)
    output_root = resolve_path(args.output_root, repo_root)
    run_id = args.run_id or default_run_id()

    if not RUN_ID_PATTERN.fullmatch(run_id):
        raise ValueError(
            "run-id must use UTC timestamp format YYYYMMDDTHHMMSSZ "
            "with an optional safe suffix"
        )
    if args.concurrency < 1 or args.concurrency > 3:
        raise ValueError("concurrency must be between 1 and 3")

    output_dir = output_root / run_id
    if output_dir.exists() and any(output_dir.iterdir()):
        raise FileExistsError(f"Refusing to overwrite non-empty run directory: {output_dir}")
    output_dir.mkdir(parents=True, exist_ok=True)

    temp_dir = repo_root / ".benchmark_tmp" / run_id
    input_file = temp_dir / "112.jsonl"

    started_at = utc_now()
    started_monotonic = time.monotonic()
    runner_exit_code = 1
    runner_error: str | None = None
    records: list[dict[str, Any]] = []

    try:
        records = load_dataset(dataset_dir, expected_count=args.expected_count)
        write_agent_input(records, input_file)

        env = os.environ.copy()
        env["LOCAL_MAX_CONCURRENCY"] = str(args.concurrency)

        command = [
            sys.executable,
            str(repo_root / "main.py"),
            "--input_file",
            str(input_file),
            "--output_dir",
            str(output_dir),
        ]
        completed = subprocess.run(command, cwd=repo_root, env=env, check=False)
        runner_exit_code = completed.returncode
    except Exception as exc:  # Keep metadata even when preparation or runner fails.
        runner_error = f"{type(exc).__name__}: {exc}"
        runner_exit_code = 1
    finally:
        finished_at = utc_now()
        duration_seconds = round(time.monotonic() - started_monotonic, 3)

        summary = build_summary(
            records,
            output_dir,
            run_id=run_id,
            runner_exit_code=runner_exit_code,
        )
        write_json(output_dir / "summary.json", summary)

        metadata = {
            "run_id": run_id,
            "started_at_utc": format_utc(started_at),
            "finished_at_utc": format_utc(finished_at),
            "duration_seconds": duration_seconds,
            "model": os.environ.get("INTERN_MODEL", "intern-s2-preview"),
            "concurrency": args.concurrency,
            "repository_commit": get_repository_commit(repo_root),
            "dataset": {
                "repository": args.dataset_repository,
                "ref": args.dataset_ref,
                "commit": args.dataset_commit,
                "path": str(args.dataset_path),
                "item_count": len(records),
                "sha256": dataset_digest(records) if records else None,
            },
            "runner_exit_code": runner_exit_code,
            "runner_error": runner_error,
            "output_directory": str(output_dir.relative_to(repo_root)),
        }
        write_json(output_dir / "run_metadata.json", metadata)
        shutil.rmtree(temp_dir, ignore_errors=True)

    print(f"Benchmark output: {output_dir}")
    return runner_exit_code


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the public 112-question math benchmark into output/<run-id>/."
    )
    parser.add_argument(
        "--dataset-dir",
        type=Path,
        required=True,
        help="Directory containing the numbered JSON files.",
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("output"),
        help="Repository-relative output root.",
    )
    parser.add_argument(
        "--run-id",
        help="UTC run folder name; defaults to YYYYMMDDTHHMMSSZ.",
    )
    parser.add_argument(
        "--concurrency",
        type=int,
        default=3,
        help="Number of questions processed concurrently (1-3).",
    )
    parser.add_argument(
        "--expected-count",
        type=int,
        default=112,
        help="Fail fast when the dataset item count differs.",
    )
    parser.add_argument(
        "--dataset-repository",
        default="Jialiang-Zhang/test-dataset-math",
    )
    parser.add_argument("--dataset-ref", default="main")
    parser.add_argument("--dataset-commit")
    parser.add_argument("--dataset-path", default="112")
    return parser.parse_args()


def main() -> None:
    raise SystemExit(run_benchmark(parse_args()))


if __name__ == "__main__":
    main()
