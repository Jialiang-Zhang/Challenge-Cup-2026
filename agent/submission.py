from __future__ import annotations

import re

from .canonicalize import normalize_answer_text
from .models import SolutionCapsule, TaskContract
from .parsing import strip_protocol_tags
from .task_profile import normalized_choice_letters


_DERIVATION_SIGNAL = re.compile(
    r"(?:证明|推导|说明为什么|解释为什么|说明理由|给出理由|验证(?:其)?关系|并验证|"
    r"严格说明|严格推导|prove|derive|explain\s+why|justify|verify)",
    flags=re.IGNORECASE,
)


def _clean_answer(capsule: SolutionCapsule, contract: TaskContract) -> str:
    answer = strip_protocol_tags(capsule.answer_raw).strip()
    if contract.question_mode == "choice":
        letters = normalized_choice_letters(answer)
        if letters:
            answer = ",".join(letters)
    elif contract.question_mode == "true_false":
        answer = answer.rstrip("。.!！").strip()

    answer = re.sub(r"^\s*(?:最终答案|答案|结论)\s*[:：]\s*", "", answer).strip()
    if not normalize_answer_text(answer):
        raise ValueError("selected candidate normalizes to an empty answer")
    return answer


def _clean_body(body: str, answer: str) -> str:
    text = strip_protocol_tags(body).strip()
    if not text:
        return ""

    lines = text.splitlines()
    if lines:
        first = lines[0].strip()
        labelled = re.match(r"^(?:最终答案|答案|结论)\s*[:：]\s*(.*)$", first)
        if labelled:
            lines = lines[1:]
        elif normalize_answer_text(first) == normalize_answer_text(answer):
            lines = lines[1:]
    return "\n".join(lines).strip()


def _trim_at_boundary(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    if limit <= 0:
        return ""

    window = text[:limit]
    floor = max(0, int(limit * 0.6))
    candidates = [
        window.rfind("\n\n", floor),
        window.rfind("。", floor),
        window.rfind(". ", floor),
        window.rfind("；", floor),
        window.rfind("; ", floor),
    ]
    cut = max(candidates)
    if cut <= floor:
        cut = limit
    elif window[cut : cut + 2] == ". ":
        cut += 1
    else:
        cut += 1
    return window[:cut].rstrip()


def _requires_derivation(
    contract: TaskContract,
    explicit_requirements: tuple[str, ...],
) -> bool:
    if contract.requires_proof or contract.answer_schema == "proof":
        return True
    if "derivation_chain" in contract.answer_obligations:
        return True
    return any(_DERIVATION_SIGNAL.search(item or "") for item in explicit_requirements)


def build_submission(
    capsule: SolutionCapsule,
    contract: TaskContract,
    *,
    explicit_requirements: tuple[str, ...] = (),
    max_chars: int = 6000,
) -> str:
    """Build the external competition response from a frozen internal candidate.

    Internal XML-like protocol fields never leak into the submitted answer. The
    final layer is deterministic: objective and ordinary calculation tasks get a
    short answer template, proof tasks get conclusion + proof, and tasks that
    explicitly demand a derivation/explanation get answer + derivation.
    """

    answer = _clean_answer(capsule, contract)
    body = _clean_body(capsule.final_response, answer)
    needs_derivation = _requires_derivation(contract, explicit_requirements)

    if contract.requires_proof or contract.answer_schema == "proof":
        prefix = f"结论：{answer}\n\n证明过程：\n"
        if not body:
            raise ValueError("proof submission requires a non-empty proof body")
        body = _trim_at_boundary(body, max_chars - len(prefix))
        result = prefix + body
    elif needs_derivation:
        prefix = f"最终答案：{answer}\n\n推导概要：\n"
        if not body:
            raise ValueError("derivation submission requires a non-empty derivation body")
        body = _trim_at_boundary(body, max_chars - len(prefix))
        result = prefix + body
    else:
        result = f"最终答案：{answer}"

    result = result.strip()
    if not result:
        raise ValueError("submission builder produced an empty response")
    return result[:max_chars].rstrip()
