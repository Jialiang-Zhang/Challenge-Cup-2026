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
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Sequence


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from agent.canonicalize import compare_answers  # noqa: E402
from agent.routing import build_task_contract  # noqa: E402


RUN_ID_PATTERN = re.compile(r"^\d{8}T\d{6}Z(?:-[A-Za-z0-9._-]+)?$")


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def format_utc(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def default_run_id() -> str:
    return utc_now().strftime("%Y%m%dT%H%M%SZ-hard3")


def parse_indices(value: str) -> tuple[int, ...]:
    parts = [part.strip() for part in value.split(",") if part.strip()]
    if not parts:
        raise ValueError("at least one dataset index is required")
    indices: list[int] = []
    for part in parts:
        if not part.isdigit():
            raise ValueError(f"invalid dataset index: {part!r}")
        idx = int(part)
        if idx in indices:
            raise ValueError(f"duplicate dataset index: {idx}")
        indices.append(idx)
    return tuple(indices)


def resolve_path(path: Path) -> Path:
    return path if path.is_absolute() else (REPO_ROOT / path).resolve()


def load_selected_dataset(
    dataset_dir: Path,
    indices: Sequence[int],
) -> list[dict[str, Any]]:
    if not dataset_dir.is_dir():
        raise FileNotFoundError(f"dataset directory does not exist: {dataset_dir}")

    records: list[dict[str, Any]] = []
    for idx in indices:
        path = dataset_dir / f"{idx}.json"
        if not path.is_file():
            raise FileNotFoundError(f"missing dataset item: {path}")
        try:
            item = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ValueError(f"invalid JSON in {path}: {exc}") from exc
        if not isinstance(item, dict):
            raise ValueError(f"dataset item must be an object: {path}")
        if item.get("idx") != idx:
            raise ValueError(
                f"dataset file/index mismatch: expected {idx}, found {item.get('idx')!r}"
            )
        problem = item.get("problem")
        if not isinstance(problem, str) or not problem.strip():
            raise ValueError(f"problem must be a non-empty string: {path}")
        records.append(item)
    return records


def write_agent_input(records: Sequence[dict[str, Any]], input_file: Path) -> None:
    """Write only idx/problem so references never enter ReasoningAgent.solve."""

    input_file.parent.mkdir(parents=True, exist_ok=True)
    with input_file.open("w", encoding="utf-8") as file:
        for item in records:
            safe_item = {"idx": item["idx"], "problem": item["problem"]}
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
            "error": {"type": type(exc).__name__, "message": str(exc)},
        }
    return value if isinstance(value, dict) else {"status": "invalid_record"}


def last_trace_content(result: dict[str, Any], step_name: str) -> dict[str, Any]:
    trace = result.get("trace", [])
    if not isinstance(trace, list):
        return {}
    for entry in reversed(trace):
        if isinstance(entry, dict) and entry.get("step") == step_name:
            content = entry.get("content", {})
            return content if isinstance(content, dict) else {}
    return {}


def build_summary(
    records: Sequence[dict[str, Any]],
    output_dir: Path,
    *,
    run_id: str,
    runner_exit_code: int,
) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    success_count = 0

    for item in records:
        idx = int(item["idx"])
        result_path = output_dir / f"{idx}.json"
        result = read_json_object(result_path) if result_path.exists() else {}
        status = str(result.get("status") or "missing")
        final_response = result.get("final_response", "")
        final_response = final_response if isinstance(final_response, str) else ""
        reference = str(item.get("answer", ""))
        relation = compare_answers(reference, final_response) if reference else "unknown"
        transaction = last_trace_content(result, "transaction_commit")
        gate = last_trace_content(result, "candidate_gate")
        red_results = [
            entry.get("content", {})
            for entry in result.get("trace", [])
            if isinstance(entry, dict) and entry.get("step") == "red_team_result"
        ]
        contract = build_task_contract(str(item["problem"]))

        success_count += int(status == "success")
        rows.append(
            {
                "idx": idx,
                "subject": str(item.get("subject") or "unknown"),
                "status": status,
                "requires_proof": contract.requires_proof,
                "risk": contract.risk_level,
                "route": contract.route_hint,
                "reference_relation": relation,
                "manual_review_required": contract.requires_proof or relation != "equivalent",
                "response_chars": len(final_response),
                "model_calls": transaction.get("model_calls"),
                "repair_count": transaction.get("repair_count"),
                "selected_candidate_id": transaction.get("candidate_id"),
                "selected_source": transaction.get("source"),
                "valid_candidate_ids": gate.get("valid_candidate_ids", []),
                "invalid_candidate_ids": gate.get("invalid_candidate_ids", []),
                "red_team_verdicts": [
                    value.get("verdict")
                    for value in red_results
                    if isinstance(value, dict)
                ],
                "output_file": f"{idx}.json",
                "error_type": (
                    result.get("error", {}).get("type")
                    if isinstance(result.get("error"), dict)
                    else None
                ),
            }
        )

    return {
        "run_id": run_id,
        "indices": [int(item["idx"]) for item in records],
        "total": len(records),
        "success_count": success_count,
        "runner_exit_code": runner_exit_code,
        "warning": (
            "Reference relation is a local heuristic. Proof quality requires manual review; "
            "this is not the official judge."
        ),
        "records": rows,
    }


def write_review_markdown(
    records: Sequence[dict[str, Any]],
    output_dir: Path,
    summary: dict[str, Any],
) -> None:
    summary_by_idx = {
        int(row["idx"]): row for row in summary.get("records", []) if isinstance(row, dict)
    }
    lines = [
        "# HORA-Math hard3 review",
        "",
        "> The reference answers are public benchmark data and were never passed to the agent.",
        "> Automated relation checks are heuristic; inspect proof logic manually.",
        "",
    ]
    for item in records:
        idx = int(item["idx"])
        result = read_json_object(output_dir / f"{idx}.json")
        final_response = str(result.get("final_response", ""))
        row = summary_by_idx.get(idx, {})
        lines.extend(
            [
                f"## idx {idx} — {item.get('subject', 'unknown')}",
                "",
                f"- Status: `{row.get('status', 'missing')}`",
                f"- Route: `{row.get('route', 'unknown')}`",
                f"- Model calls: `{row.get('model_calls')}`",
                f"- Repair count: `{row.get('repair_count')}`",
                f"- Local reference relation: `{row.get('reference_relation', 'unknown')}`",
                "",
                "### Problem",
                "",
                str(item["problem"]),
                "",
                "### Agent final response",
                "",
                final_response or "_missing_",
                "",
                "### Public reference answer",
                "",
                str(item.get("answer", "_missing_")),
                "",
            ]
        )
    (output_dir / "review.md").write_text("\n".join(lines), encoding="utf-8")


def get_repository_commit() -> str | None:
    try:
        completed = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=REPO_ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        value = completed.stdout.strip()
        return value or None
    except (OSError, subprocess.CalledProcessError):
        return os.environ.get("GITHUB_SHA")


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def run_benchmark(args: argparse.Namespace) -> int:
    dataset_dir = resolve_path(args.dataset_dir)
    output_root = resolve_path(args.output_root)
    indices = parse_indices(args.indices)
    run_id = args.run_id or default_run_id()

    if not RUN_ID_PATTERN.fullmatch(run_id):
        raise ValueError(
            "run-id must use UTC format YYYYMMDDTHHMMSSZ with an optional safe suffix"
        )
    if args.concurrency < 1 or args.concurrency > 3:
        raise ValueError("concurrency must be between 1 and 3")

    output_dir = output_root / run_id
    if output_dir.exists() and any(output_dir.iterdir()):
        raise FileExistsError(f"refusing to overwrite non-empty run directory: {output_dir}")
    output_dir.mkdir(parents=True, exist_ok=True)

    temp_dir = REPO_ROOT / ".benchmark_tmp" / run_id
    input_file = temp_dir / "subset.jsonl"
    records: list[dict[str, Any]] = []
    runner_exit_code = 1
    runner_error: str | None = None
    started_at = utc_now()
    started_monotonic = time.monotonic()

    try:
        records = load_selected_dataset(dataset_dir, indices)
        write_agent_input(records, input_file)
        env = os.environ.copy()
        env["LOCAL_MAX_CONCURRENCY"] = str(args.concurrency)
        completed = subprocess.run(
            [
                sys.executable,
                str(REPO_ROOT / "main.py"),
                "--input_file",
                str(input_file),
                "--output_dir",
                str(output_dir),
            ],
            cwd=REPO_ROOT,
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
        write_json(output_dir / "summary.json", summary)
        write_review_markdown(records, output_dir, summary)
        metadata = {
            "run_id": run_id,
            "started_at_utc": format_utc(started_at),
            "finished_at_utc": format_utc(finished_at),
            "duration_seconds": duration_seconds,
            "model": os.environ.get("INTERN_MODEL", "intern-s2-preview"),
            "concurrency": args.concurrency,
            "repository_commit": get_repository_commit(),
            "dataset": {
                "repository": args.dataset_repository,
                "ref": args.dataset_ref,
                "commit": args.dataset_commit,
                "path": str(args.dataset_path),
                "indices": list(indices),
                "sha256": dataset_digest(records) if records else None,
            },
            "runner_exit_code": runner_exit_code,
            "runner_error": runner_error,
            "output_directory": str(output_dir.relative_to(REPO_ROOT)),
        }
        write_json(output_dir / "run_metadata.json", metadata)
        shutil.rmtree(temp_dir, ignore_errors=True)

    summary = read_json_object(output_dir / "summary.json")
    if runner_exit_code != 0 or summary.get("success_count") != len(records):
        return 1
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a small public math subset into output/<run-id>/."
    )
    parser.add_argument("--dataset-dir", type=Path, required=True)
    parser.add_argument("--indices", default="0,40,70")
    parser.add_argument("--output-root", type=Path, default=Path("output"))
    parser.add_argument("--run-id")
    parser.add_argument("--concurrency", type=int, default=1)
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
