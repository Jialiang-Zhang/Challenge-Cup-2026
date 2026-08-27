from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from llm_client import InternChatClient  # noqa: E402


VALID_VERDICTS = {"CORRECT", "INCORRECT"}


def extract_tag(text: str, tag: str) -> str:
    matches = re.findall(
        rf"<{re.escape(tag)}>\s*(.*?)\s*</{re.escape(tag)}>",
        text,
        flags=re.IGNORECASE | re.DOTALL,
    )
    return matches[-1].strip() if matches else ""


def parse_judge_response(text: str) -> tuple[str, str, bool]:
    raw_verdict = extract_tag(text, "VERDICT").upper().strip()
    reason = extract_tag(text, "REASON").strip()
    parsed = raw_verdict in VALID_VERDICTS and bool(reason)
    if not parsed:
        return "INCORRECT", "judge output was not valid structured output", False
    return raw_verdict, reason[:1600], True


def build_prompt(
    *,
    problem: str,
    reference: str,
    candidate: str,
    judge_kind: str,
) -> str:
    if judge_kind == "completeness":
        role = (
            "你是严格的数学竞赛判题员。你的任务不是寻找措辞相似，而是判断候选答案是否在数学上完整满足题目。"
            "逐项核对题目显式要求、最终结论、证明义务、构造或解释。"
        )
    else:
        role = (
            "你是对抗性数学审查员。先假设候选可能存在隐藏错误，主动寻找第一个能使答案失效的实质问题："
            "定理条件缺失、错误反例、边界/退化情形、量词错误、循环论证、非法变形、只得到正确结论但证明错误等。"
            "只有在尝试攻击后仍找不到实质错误时才判 CORRECT。"
        )

    return f"""{role}

严格判定规则：
1. 下方参考答案是一份可信标准答案；候选允许使用与参考答案不同但数学等价且完整的方法。
2. 若题目要求“证明、解释、说明、构造、严格证明”等，候选必须完成这些义务。只给最终公式或结论，判 INCORRECT。
3. 若证明中存在会破坏证明有效性的数学错误，即使最终结论碰巧正确，也判 INCORRECT。
4. 选择题、数值题、填空题允许等价数学表达；必须准确回答题目要求的全部选项/数值/对象。
5. 多小问必须全部覆盖。必要性/充分性、存在性/唯一性等若题目均有要求，不能遗漏。
6. 不能因为语言、排版、推导顺序与参考不同而误判。
7. 如果无法从候选中确认某个必要步骤成立，采用严格口径，判 INCORRECT。
8. 不评价 trace，不猜测候选未写出的思考；只评价 final_response 的数学内容。

【题目】
{problem}

【参考答案】
{reference}

【候选 final_response】
{candidate}

只输出以下结构，不要在标签外输出任何文字：
<VERDICT>CORRECT</VERDICT>
<REASON>若正确，概括为何满足全部要求；若错误，指出第一个决定性的数学错误或缺失义务。300字以内。</REASON>

如果候选不正确，将 VERDICT 改为 INCORRECT。
"""


def run_one_judge(
    *,
    idx: int,
    judge_id: int,
    problem: str,
    reference: str,
    candidate: str,
) -> dict[str, Any]:
    judge_kind = "completeness" if judge_id == 1 else "adversarial"
    client = InternChatClient(timeout=120, retry=3)
    prompt = build_prompt(
        problem=problem,
        reference=reference,
        candidate=candidate,
        judge_kind=judge_kind,
    )
    try:
        response = client.chat(
            [{"role": "user", "content": prompt}],
            temperature=0.0 if judge_id == 1 else 0.1,
            max_tokens=1800,
            thinking_mode=True,
        )
        text = response if isinstance(response, str) else json.dumps(response, ensure_ascii=False)
        verdict, reason, parsed = parse_judge_response(text)
        return {
            "idx": idx,
            "judge_id": judge_id,
            "judge_kind": judge_kind,
            "verdict": verdict,
            "reason": reason,
            "parsed": parsed,
            "error_type": None,
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "idx": idx,
            "judge_id": judge_id,
            "judge_kind": judge_kind,
            "verdict": "INCORRECT",
            "reason": f"judge call failed: {type(exc).__name__}: {exc}",
            "parsed": False,
            "error_type": type(exc).__name__,
        }


def read_object(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        return {"status": "unreadable", "error": f"{type(exc).__name__}: {exc}"}
    return value if isinstance(value, dict) else {"status": "invalid"}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--concurrency", type=int, default=16)
    parser.add_argument("--agent-commit", required=True)
    parser.add_argument("--dataset-commit", required=True)
    args = parser.parse_args()

    if args.concurrency < 1:
        raise ValueError("concurrency must be positive")

    dataset_dir = args.dataset_dir.resolve()
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    records: dict[int, dict[str, Any]] = {}
    futures = []
    execution_success = 0

    for idx in range(112):
        reference_record = read_object(dataset_dir / f"{idx}.json")
        result = read_object(output_dir / f"{idx}.json")
        subject = str(reference_record.get("subject") or "unknown")
        status = str(result.get("status") or "missing")
        final_response = result.get("final_response", "")
        candidate = final_response if isinstance(final_response, str) else ""

        record: dict[str, Any] = {
            "idx": idx,
            "subject": subject,
            "execution_status": status,
            "response_chars": len(candidate),
            "judge_1": None,
            "judge_2": None,
        }
        records[idx] = record

        if status == "success" and candidate.strip():
            execution_success += 1
        else:
            reason = f"execution did not yield a non-empty success result: {status}"
            record["judge_1"] = {
                "judge_kind": "completeness",
                "verdict": "INCORRECT",
                "reason": reason,
                "parsed": True,
                "error_type": None,
            }
            record["judge_2"] = {
                "judge_kind": "adversarial",
                "verdict": "INCORRECT",
                "reason": reason,
                "parsed": True,
                "error_type": None,
            }

    with ThreadPoolExecutor(max_workers=args.concurrency) as executor:
        for idx in range(112):
            record = records[idx]
            if record["execution_status"] != "success":
                continue
            reference_record = read_object(dataset_dir / f"{idx}.json")
            result = read_object(output_dir / f"{idx}.json")
            candidate = result.get("final_response", "")
            if not isinstance(candidate, str) or not candidate.strip():
                continue
            problem = str(reference_record.get("problem") or "")
            reference = str(reference_record.get("answer") or "")
            for judge_id in (1, 2):
                future = executor.submit(
                    run_one_judge,
                    idx=idx,
                    judge_id=judge_id,
                    problem=problem,
                    reference=reference,
                    candidate=candidate,
                )
                futures.append(future)

        for future in as_completed(futures):
            judgment = future.result()
            idx = int(judgment.pop("idx"))
            judge_id = int(judgment.pop("judge_id"))
            records[idx][f"judge_{judge_id}"] = judgment
            print(
                f"strict judge idx={idx} pass={judge_id} verdict={judgment['verdict']}",
                flush=True,
            )

    strict_correct = 0
    judge_disagreements: list[int] = []
    parsing_failures = 0
    judge_call_errors = 0
    per_subject: dict[str, dict[str, int]] = defaultdict(
        lambda: {
            "total": 0,
            "execution_success": 0,
            "strict_correct": 0,
            "strict_incorrect": 0,
        }
    )

    final_records: list[dict[str, Any]] = []
    for idx in range(112):
        record = records[idx]
        j1 = record.get("judge_1") or {
            "verdict": "INCORRECT",
            "reason": "missing judge 1",
            "parsed": False,
            "error_type": "MissingJudge",
        }
        j2 = record.get("judge_2") or {
            "verdict": "INCORRECT",
            "reason": "missing judge 2",
            "parsed": False,
            "error_type": "MissingJudge",
        }
        record["judge_1"] = j1
        record["judge_2"] = j2

        v1 = str(j1.get("verdict") or "INCORRECT")
        v2 = str(j2.get("verdict") or "INCORRECT")
        agreement = v1 == v2
        strict_verdict = "CORRECT" if v1 == "CORRECT" and v2 == "CORRECT" else "INCORRECT"
        record["judge_agreement"] = agreement
        record["strict_verdict"] = strict_verdict

        if not agreement:
            judge_disagreements.append(idx)
        if not bool(j1.get("parsed", False)):
            parsing_failures += 1
        if not bool(j2.get("parsed", False)):
            parsing_failures += 1
        if j1.get("error_type"):
            judge_call_errors += 1
        if j2.get("error_type"):
            judge_call_errors += 1

        subject = str(record.get("subject") or "unknown")
        bucket = per_subject[subject]
        bucket["total"] += 1
        if record["execution_status"] == "success":
            bucket["execution_success"] += 1
        if strict_verdict == "CORRECT":
            strict_correct += 1
            bucket["strict_correct"] += 1
        else:
            bucket["strict_incorrect"] += 1
        final_records.append(record)

    summary = {
        "total": 112,
        "agent_commit": args.agent_commit,
        "dataset_commit": args.dataset_commit,
        "agent_concurrency": 16,
        "judge_concurrency": args.concurrency,
        "execution_success": execution_success,
        "execution_errors_or_empty": 112 - execution_success,
        "execution_success_rate": execution_success / 112,
        "strict_correct": strict_correct,
        "strict_incorrect": 112 - strict_correct,
        "strict_accuracy": strict_correct / 112,
        "strict_accuracy_among_executed_successes": (
            strict_correct / execution_success if execution_success else 0.0
        ),
        "strict_rule": (
            "execution failures count incorrect; each successful final_response is judged independently "
            "by a completeness judge and an adversarial judge; only unanimous CORRECT counts as correct"
        ),
        "judge_disagreement_count": len(judge_disagreements),
        "judge_disagreements": judge_disagreements,
        "judge_parse_failure_count": parsing_failures,
        "judge_call_error_count": judge_call_errors,
        "per_subject": dict(sorted(per_subject.items())),
        "warning": (
            "This is a conservative local strict double-judge diagnostic using Intern-S and the public "
            "reference answers. It is not the official competition judge score."
        ),
    }

    (output_dir / "strict_judgements.json").write_text(
        json.dumps(final_records, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (output_dir / "strict_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
