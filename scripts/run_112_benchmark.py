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

from agent.canonicalize import compare_answers, normalize_answer_text


RUN_ID_PATTERN = re.compile(r"^\d{8}T\d{6}Z(?:-[A-Za-z0-9._-]+)?$")


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def format_utc(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def default_run_id() -> str:
    return utc_now().strftime("%Y%m%dT%H%M%SZ")


def resolve_path(path: Path, repo_root: Path) -> Path:
    return path if path.is_absolute() else (repo_root / path).resolve()


def display_path(path: Path, repo_root: Path) -> str:
    try:
        return str(path.relative_to(repo_root))
    except ValueError:
        return str(path)


def load_dataset(
    dataset_dir: Path, expected_count: int | None = 112
) -> list[dict[str, Any]]:
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
    if expected_count is not None:
        if len(records) != expected_count:
            raise ValueError(
                f"Expected {expected_count} dataset items, found {len(records)} in {dataset_dir}"
            )
        expected_indices = set(range(expected_count))
        if seen_indices != expected_indices:
            raise ValueError(
                "Dataset indices must be exactly "
                f"0..{expected_count - 1}; "
                f"missing={sorted(expected_indices - seen_indices)}, "
                f"unexpected={sorted(seen_indices - expected_indices)}"
            )
    return records


def write_agent_input(records: Sequence[dict[str, Any]], input_file: Path) -> None:
    """Write only idx/problem so reference answers never reach ReasoningAgent."""
    input_file.parent.mkdir(parents=True, exist_ok=True)
    with input_file.open("w", encoding="utf-8") as file:
        for item in records:
            file.write(
                json.dumps(
                    {"idx": item["idx"], "problem": item["problem"]},
                    ensure_ascii=False,
                )
                + "\n"
            )


def dataset_digest(records: Iterable[dict[str, Any]]) -> str:
    digest = hashlib.sha256()
    for item in records:
        digest.update(
            json.dumps(
                item,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        )
        digest.update(b"\n")
    return digest.hexdigest()


def read_json_object(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {
            "status": "unreadable",
            "error": {"type": type(exc).__name__, "message": str(exc)},
        }
    return value if isinstance(value, dict) else {"status": "invalid_record"}


def _trace_content(trace: Any, step_name: str, *, reverse: bool = False) -> dict[str, Any]:
    if not isinstance(trace, list):
        return {}
    entries = reversed(trace) if reverse else trace
    for entry in entries:
        if isinstance(entry, dict) and entry.get("step") == step_name:
            content = entry.get("content")
            return content if isinstance(content, dict) else {}
    return {}


def _reference_relation(reference: Any, final_response: str) -> str:
    if not isinstance(reference, str) or not reference.strip() or not final_response.strip():
        return "unavailable"
    relation = compare_answers(reference, final_response)
    if relation != "unknown":
        return relation
    normalized_reference = normalize_answer_text(reference)
    normalized_final = normalize_answer_text(final_response)
    if (
        normalized_reference
        and len(normalized_reference) <= 240
        and normalized_reference.casefold() in normalized_final.casefold()
    ):
        return "text_match"
    return "unknown"


def build_summary(
    records: Sequence[dict[str, Any]],
    output_dir: Path,
    *,
    run_id: str,
    runner_exit_code: int,
) -> dict[str, Any]:
    per_item: list[dict[str, Any]] = []
    status_counts: Counter[str] = Counter()
    subject_counts: Counter[str] = Counter()
    route_counts: Counter[str] = Counter()
    risk_counts: Counter[str] = Counter()
    domain_counts: Counter[str] = Counter()
    orthogonality_counts: Counter[str] = Counter()
    candidate_equivalence_counts: Counter[str] = Counter()
    red_team_counts: Counter[str] = Counter()
    reference_counts: Counter[str] = Counter()
    source_counts: Counter[str] = Counter()
    model_calls_total = 0
    repair_total = 0

    for item in records:
        idx = item["idx"]
        subject = str(item.get("subject") or "unknown")
        subject_counts[subject] += 1
        result_path = output_dir / f"{idx}.json"
        if result_path.exists():
            result = read_json_object(result_path)
            status = str(result.get("status") or "unknown")
        else:
            result = {}
            status = "missing"

        final_response = result.get("final_response", "")
        final_response = final_response if isinstance(final_response, str) else ""
        trace = result.get("trace", [])
        error = result.get("error", {})
        error_type = error.get("type") if isinstance(error, dict) else None

        profile = _trace_content(trace, "profile")
        comparison = _trace_content(trace, "orthogonal_comparison")
        red_team = _trace_content(trace, "red_team_result", reverse=True)
        transaction = _trace_content(trace, "transaction_commit", reverse=True)

        route = str(profile.get("route") or "unknown")
        risk = str(profile.get("risk") or "unknown")
        domain = str(profile.get("domain") or "unknown")
        orthogonality = str(comparison.get("orthogonality") or "not_run")
        candidate_equivalence = str(comparison.get("equivalence") or "not_run")
        red_team_verdict = str(red_team.get("verdict") or "not_run")
        selected_source = str(transaction.get("source") or "unknown")
        model_calls = int(transaction.get("model_calls") or 0)
        repair_count = int(transaction.get("repair_count") or 0)
        reference_relation = _reference_relation(item.get("answer"), final_response)

        status_counts[status] += 1
        route_counts[route] += 1
        risk_counts[risk] += 1
        domain_counts[domain] += 1
        orthogonality_counts[orthogonality] += 1
        candidate_equivalence_counts[candidate_equivalence] += 1
        red_team_counts[red_team_verdict] += 1
        reference_counts[reference_relation] += 1
        source_counts[selected_source] += 1
        model_calls_total += model_calls
        repair_total += repair_count

        per_item.append(
            {
                "idx": idx,
                "subject": subject,
                "status": status,
                "route": route,
                "risk": risk,
                "domain": domain,
                "orthogonality": orthogonality,
                "candidate_equivalence": candidate_equivalence,
                "red_team_verdict": red_team_verdict,
                "selected_source": selected_source,
                "model_calls": model_calls,
                "repair_count": repair_count,
                "reference_relation": reference_relation,
                "response_chars": len(final_response),
                "trace_steps": len(trace) if isinstance(trace, list) else 0,
                "error_type": error_type,
                "output_file": f"{idx}.json",
            }
        )

    total = len(records)
    success_count = status_counts.get("success", 0)
    return {
        "run_id": run_id,
        "architecture": "HORA-Math-v1",
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
        "telemetry": {
            "model_calls_total": model_calls_total,
            "model_calls_average": model_calls_total / total if total else 0.0,
            "repair_total": repair_total,
            "routes": dict(sorted(route_counts.items())),
            "risks": dict(sorted(risk_counts.items())),
            "domains": dict(sorted(domain_counts.items())),
            "orthogonality": dict(sorted(orthogonality_counts.items())),
            "candidate_equivalence": dict(sorted(candidate_equivalence_counts.items())),
            "red_team_verdicts": dict(sorted(red_team_counts.items())),
            "selected_sources": dict(sorted(source_counts.items())),
        },
        "reference_evaluation": {
            "counts": dict(sorted(reference_counts.items())),
            "warning": (
                "Reference equivalence is a conservative local diagnostic and is not the "
                "official mathematical judge. Long proofs normally remain unknown."
            ),
        },
        "subjects": dict(sorted(subject_counts.items())),
        "records": per_item,
    }


def derive_benchmark_exit_code(summary: dict[str, Any], runner_exit_code: int) -> int:
    if runner_exit_code != 0:
        return runner_exit_code
    total = int(summary.get("total", 0))
    counts = summary.get("counts", {})
    success_count = int(counts.get("success", 0)) if isinstance(counts, dict) else 0
    return 0 if success_count == total else 2


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
    if completed is not None and completed.stdout.strip():
        return completed.stdout.strip()
    return os.environ.get("GITHUB_SHA") or None


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def run_benchmark(args: argparse.Namespace) -> int:
    repo_root = Path(__file__).resolve().parents[1]
    dataset_dir = resolve_path(args.dataset_dir, repo_root)
    output_root = resolve_path(args.output_root, repo_root)
    run_id = args.run_id or default_run_id()
    if not RUN_ID_PATTERN.fullmatch(run_id):
        raise ValueError(
            "run-id must use UTC timestamp format YYYYMMDDTHHMMSSZ with an optional safe suffix"
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
        completed = subprocess.run(
            [
                sys.executable,
                str(repo_root / "main.py"),
                "--input_file",
                str(input_file),
                "--output_dir",
                str(output_dir),
            ],
            cwd=repo_root,
            env=env,
            check=False,
        )
        runner_exit_code = completed.returncode
    except Exception as exc:
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
        final_exit_code = derive_benchmark_exit_code(summary, runner_exit_code)
        if final_exit_code != runner_exit_code and runner_error is None:
            counts = summary["counts"]
            runner_error = (
                "Incomplete benchmark outputs: "
                f"success={counts['success']}, error={counts['error']}, "
                f"missing={counts['missing']}, other={counts['other']}"
            )
        runner_exit_code = final_exit_code
        summary["runner_exit_code"] = runner_exit_code
        write_json(output_dir / "summary.json", summary)
        write_json(
            output_dir / "run_metadata.json",
            {
                "run_id": run_id,
                "architecture": "HORA-Math-v1",
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
                "output_directory": display_path(output_dir, repo_root),
            },
        )
        shutil.rmtree(temp_dir, ignore_errors=True)

    print(f"Benchmark output: {output_dir}")
    return runner_exit_code


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the public 112-question math benchmark into output/<run-id>/."
    )
    parser.add_argument("--dataset-dir", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, default=Path("output"))
    parser.add_argument("--run-id")
    parser.add_argument("--concurrency", type=int, default=3)
    parser.add_argument("--expected-count", type=int, default=112)
    parser.add_argument(
        "--dataset-repository", default="Jialiang-Zhang/test-dataset-math"
    )
    parser.add_argument("--dataset-ref", default="main")
    parser.add_argument("--dataset-commit")
    parser.add_argument("--dataset-path", default="112")
    return parser.parse_args()


def main() -> None:
    raise SystemExit(run_benchmark(parse_args()))


if __name__ == "__main__":
    main()
