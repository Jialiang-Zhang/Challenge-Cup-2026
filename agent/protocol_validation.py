from __future__ import annotations

import re

from .canonicalize import compare_answers
from .models import SolutionCapsule
from .parsing import extract_final_candidate


_EXACT_PLACEHOLDERS = {
    "answer",
    "answer here",
    "actual answer",
    "exact answer",
    "exact independent answer",
    "corrected exact answer",
    "concise answer",
    "submission ready answer",
    "first decisive claim",
    "minimal decisive justification",
    "none",
}

_PREFIX_PLACEHOLDERS = (
    "put the exact final",
    "give a concise exact answer",
    "give a concise independent proof",
    "submission ready corrected answer",
    "concise submission ready answer",
    "write the actual",
    "state the actual",
    "list checks that",
    "list unresolved risks",
)


def _instruction_key(value: str) -> str:
    value = re.sub(r"<[^>]+>", " ", value)
    value = value.replace("`", " ").replace("_", " ")
    value = re.sub(r"[^0-9A-Za-z\u4e00-\u9fff]+", " ", value)
    return re.sub(r"\s+", " ", value).strip().lower()


def is_protocol_placeholder(value: str | None) -> bool:
    if value is None:
        return True
    raw = value.strip()
    if not raw or raw in {"...", "…", "[...]", "[…]"}:
        return True
    key = _instruction_key(raw)
    if not key:
        return True
    if key in _EXACT_PLACEHOLDERS:
        return True
    return any(key.startswith(prefix) for prefix in _PREFIX_PLACEHOLDERS)


def leading_response_answer(value: str | None) -> str | None:
    """Read the exact-answer line required at the start of FINAL_RESPONSE."""

    if value is None:
        return None
    lines = [line.strip() for line in value.splitlines() if line.strip()]
    if not lines:
        return None
    # Remove true Markdown bullets only. A mathematical negative sign such as
    # ``-1`` or ``-\frac{1}{8}`` must be preserved.
    first = re.sub(r"^(?:[*•]\s*|-\s+)", "", lines[0]).strip()
    if len(first) > 300 or is_protocol_placeholder(first):
        return None
    return first


def sanitize_solution_capsule(
    capsule: SolutionCapsule,
    *,
    requires_proof: bool,
) -> SolutionCapsule:
    """Reject placeholders and reconcile exact answers with FINAL_RESPONSE."""

    warnings = list(capsule.parse_warnings)
    answer = capsule.answer_raw.strip()
    response = capsule.final_response.strip()

    if is_protocol_placeholder(answer):
        recovered = None
        if response and not is_protocol_placeholder(response):
            recovered = extract_final_candidate(response)
        if recovered and not is_protocol_placeholder(recovered):
            answer = recovered.strip()
            warnings.append("recovered_answer_from_final_response")
        else:
            answer = ""
            warnings.append("placeholder_final_candidate")

    if is_protocol_placeholder(response):
        if answer and not requires_proof:
            response = answer
            warnings.append("replaced_placeholder_final_response")
        else:
            response = ""
            warnings.append("placeholder_final_response")

    # For calculation and short-answer routes, the exact answer is required on
    # the first line of FINAL_RESPONSE. If FINAL_CANDIDATE contradicts that later
    # transaction field, the later field wins and the conflict remains in trace
    # metadata via parse_warnings.
    if not requires_proof and answer and response:
        response_answer = leading_response_answer(response)
        if response_answer:
            relation = compare_answers(answer, response_answer)
            if relation == "not_equivalent":
                answer = response_answer
                warnings.append("candidate_response_conflict")
                warnings.append("reconciled_to_final_response")

    valid_claims = []
    for claim in capsule.claims:
        if is_protocol_placeholder(claim.statement):
            warnings.append(f"placeholder_claim:{claim.claim_id}")
            continue
        valid_claims.append(claim)

    capsule.answer_raw = answer
    capsule.final_response = response
    capsule.claims = valid_claims
    capsule.parse_warnings = tuple(dict.fromkeys(warnings))
    capsule.complete = bool(answer and response)
    return capsule
