from __future__ import annotations

import re

from .canonicalize import compare_answers
from .models import SolutionCapsule
from .parsing import extract_asserted_answer, extract_final_candidate


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

_CONCISE_TEXT_ANSWERS = {
    "all real numbers",
    "does not exist",
    "no solution",
    "infinitely many",
    "true",
    "false",
    "yes",
    "no",
}


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


def _looks_like_compact_answer(value: str) -> bool:
    value = value.strip()
    if not value or len(value) > 160:
        return False
    if is_protocol_placeholder(value):
        return False

    key = _instruction_key(value)
    if key in _CONCISE_TEXT_ANSWERS:
        return True
    if re.search(
        r"\b(?:because|therefore|hence|since|by\s+the|the\s+answer\s+is)\b|"
        r"(?:因为|由于|根据|所以|从而|可得|答案为)",
        value,
        flags=re.IGNORECASE,
    ):
        return False

    latin_words = re.findall(r"[A-Za-z]{2,}", value)
    strong_math_syntax = bool(re.search(r"[=\\{}\[\]()+*/^]", value))
    if len(latin_words) > 2 and not strong_math_syntax:
        return False
    return True


def leading_response_answer(value: str | None) -> str | None:
    """Read the compact exact-answer line required at the start of FINAL_RESPONSE."""

    if value is None:
        return None
    lines = [line.strip() for line in value.splitlines() if line.strip()]
    if not lines:
        return None
    first = re.sub(r"^(?:[*•]\s*|-\s+)", "", lines[0]).strip()
    return first if _looks_like_compact_answer(first) else None


def _consistent_asserted_answer(capsule: SolutionCapsule) -> str | None:
    sources = [capsule.final_response, capsule.challenge_resolution or ""]
    sources.extend(claim.statement for claim in capsule.claims)
    if capsule.check_hints:
        sources.append("\n".join(capsule.check_hints))

    assertions: list[str] = []
    leading = leading_response_answer(capsule.final_response)
    if leading:
        assertions.append(leading)
    for source in sources:
        asserted = extract_asserted_answer(source)
        if asserted and _looks_like_compact_answer(asserted):
            assertions.append(asserted)

    unique: list[str] = []
    for value in assertions:
        if not any(compare_answers(value, existing) == "equivalent" for existing in unique):
            unique.append(value)
    return unique[0] if len(unique) == 1 else None


def sanitize_solution_capsule(
    capsule: SolutionCapsule,
    *,
    requires_proof: bool,
) -> SolutionCapsule:
    """Reject placeholders and reconcile internally asserted exact answers."""

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

    capsule.answer_raw = answer
    capsule.final_response = response

    if not requires_proof and answer and response:
        asserted = _consistent_asserted_answer(capsule)
        if asserted:
            relation = compare_answers(answer, asserted)
            if relation == "not_equivalent":
                answer = asserted
                warnings.append("candidate_internal_conflict")
                warnings.append("reconciled_to_asserted_final_answer")

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
