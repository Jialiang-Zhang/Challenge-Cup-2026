from __future__ import annotations

import re
from typing import Any

from .models import AuditResult, ClaimRecord, MethodFingerprint, SolutionCapsule


TAG_TEMPLATE = r"<{tag}(?:\s+[^>]*)?>(.*?)</{tag}>"


def coerce_text(response: Any) -> str:
    if isinstance(response, str):
        return response
    if isinstance(response, dict):
        content = response.get("content")
        if isinstance(content, str):
            return content
        message = response.get("message")
        if isinstance(message, dict) and isinstance(message.get("content"), str):
            return message["content"]
    content = getattr(response, "content", None)
    if isinstance(content, str):
        return content
    raise TypeError(f"Unsupported model response type: {type(response).__name__}")


def extract_tag(text: str, tag: str) -> str | None:
    """Return the last real protocol tag body.

    Intern-S may discuss literal protocol tags inside its reasoning. Real protocol
    sections are required to begin at the start of a line; inline/backticked tag
    mentions therefore cannot be paired with a later closing tag and corrupt the
    transaction parser.
    """

    escaped = re.escape(tag)
    opening_pattern = re.compile(
        rf"^[ \t]*<{escaped}(?:\s+[^>]*)?>",
        flags=re.IGNORECASE | re.MULTILINE,
    )
    closing_pattern = re.compile(
        rf"</{escaped}\s*>",
        flags=re.IGNORECASE,
    )
    openings = list(opening_pattern.finditer(text))
    closings = list(closing_pattern.finditer(text))
    if not openings or not closings:
        return None

    for closing in reversed(closings):
        preceding = [opening for opening in openings if opening.end() <= closing.start()]
        if not preceding:
            continue
        opening = preceding[-1]
        value = text[opening.end() : closing.start()].strip()
        if value:
            return value
    return None


def _extract_balanced_boxed(text: str) -> str | None:
    starts = [match.start() for match in re.finditer(r"\\boxed\s*\{", text)]
    for start in reversed(starts):
        brace_start = text.find("{", start)
        if brace_start < 0:
            continue
        depth = 0
        for index in range(brace_start, len(text)):
            char = text[index]
            if char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0:
                    value = text[brace_start + 1 : index].strip()
                    if value:
                        return value
                    break
    return None


def _compact_candidate(value: str) -> str:
    lines = [line.strip() for line in value.splitlines() if line.strip()]
    if not lines:
        return ""
    first = lines[0]
    if len(lines) > 1 and len(first) <= 300:
        return first
    return value.strip()


def extract_asserted_answer(text: str) -> str | None:
    """Extract a strongly asserted final/correct value from explanatory prose.

    This is intentionally narrower than generic number extraction. It is used to
    reconcile a malformed FINAL_CANDIDATE only when the model later states an
    explicit exact/correct/final value in its transaction response.
    """

    patterns = (
        re.compile(
            r"(?:exact|correct|final)\s+(?:value|answer|result)\s+(?:is|=)\s*\$([^$\n]{1,180})\$",
            flags=re.IGNORECASE,
        ),
        re.compile(
            r"(?:正确答案|最终答案|精确值|正确值|最终结果)\s*(?:是|为|=|[:：])\s*\$([^$\n]{1,180})\$",
            flags=re.IGNORECASE,
        ),
        re.compile(
            r"(?:exact|correct|final)\s+(?:value|answer|result)\s+(?:is|=)\s*"
            r"([+-]?(?:\\frac\s*\{[^{}\n]+\}\s*\{[^{}\n]+\}|\d+(?:/\d+)?(?:\.\d+)?))",
            flags=re.IGNORECASE,
        ),
        re.compile(
            r"(?:正确答案|最终答案|精确值|正确值|最终结果)\s*(?:是|为|=|[:：])\s*"
            r"([+-]?(?:\\frac\s*\{[^{}\n]+\}\s*\{[^{}\n]+\}|\d+(?:/\d+)?(?:\.\d+)?))",
            flags=re.IGNORECASE,
        ),
    )
    matches: list[tuple[int, str]] = []
    for pattern in patterns:
        for match in pattern.finditer(text):
            value = match.group(1).strip().rstrip("。.;；,")
            if value:
                matches.append((match.start(), value))
    if not matches:
        return None
    return max(matches, key=lambda item: item[0])[1]


def extract_final_candidate(text: str) -> str | None:
    tagged = extract_tag(text, "FINAL_CANDIDATE")
    if tagged:
        return _compact_candidate(tagged)

    patterns = (
        r"(?:FINAL_CANDIDATE|FINAL ANSWER|Final Answer|最终答案|答案)\s*[:：]\s*(.+)",
        r"(?:因此|故)\s*(?:答案为|结果为)\s*(.+)",
    )
    for pattern in patterns:
        matches = re.findall(pattern, text, flags=re.IGNORECASE)
        if matches:
            candidate = matches[-1].strip().splitlines()[0].strip()
            if candidate:
                return _compact_candidate(candidate)

    asserted = extract_asserted_answer(text)
    if asserted:
        return asserted

    boxed = _extract_balanced_boxed(text)
    if boxed:
        return boxed

    nonempty = [line.strip() for line in text.splitlines() if line.strip()]
    if nonempty:
        last = nonempty[-1]
        if len(last) <= 300:
            return last
    return None


def _parse_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y"}


def parse_method_fingerprint(
    text: str, fallback: MethodFingerprint
) -> MethodFingerprint:
    block = extract_tag(text, "METHOD_FINGERPRINT")
    if not block:
        return fallback

    values: dict[str, str] = {}
    for line in block.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        values[key.strip().lower()] = value.strip()

    return MethodFingerprint(
        paradigm=values.get("paradigm", fallback.paradigm),
        representation=values.get("representation", fallback.representation),
        theorem_family=values.get("theorem_family", fallback.theorem_family),
        tool_channel=values.get("tool_channel", fallback.tool_channel),
        interpretation_id=values.get("interpretation_id", fallback.interpretation_id),
        exposed_to_primary=_parse_bool(
            values.get("exposed_to_primary"), fallback.exposed_to_primary
        ),
    )


def parse_claims(text: str) -> list[ClaimRecord]:
    claims: list[ClaimRecord] = []
    block = extract_tag(text, "CRITICAL_CLAIMS")
    scope = block if block else text

    for match in re.finditer(
        r"<CLAIM(?:\s+id=[\"']?([^\"'>\s]+)[\"']?)?>(.*?)</CLAIM>",
        scope,
        flags=re.IGNORECASE | re.DOTALL,
    ):
        claim_id = (match.group(1) or f"C{len(claims) + 1}").strip()
        statement = re.sub(r"\s+", " ", match.group(2)).strip()
        if statement:
            claims.append(ClaimRecord(claim_id=claim_id, statement=statement))

    if claims:
        return claims[:8]

    if block:
        for line in block.splitlines():
            cleaned = re.sub(r"^[\s\-*\d.)、]+", "", line).strip()
            if cleaned:
                claims.append(
                    ClaimRecord(claim_id=f"C{len(claims) + 1}", statement=cleaned)
                )
    return claims[:8]


def _parse_list_block(text: str, tag: str) -> tuple[str, ...]:
    block = extract_tag(text, tag)
    if not block:
        return ()
    values: list[str] = []
    for line in re.split(r"[\n;；]+", block):
        cleaned = re.sub(r"^[\s\-*\d.)、]+", "", line).strip()
        if cleaned and cleaned.lower() != "none":
            values.append(cleaned)
    return tuple(values[:8])


def strip_protocol_tags(text: str) -> str:
    cleaned = re.sub(r"</?[A-Z_]+(?:\s+[^>]*)?>", "", text, flags=re.IGNORECASE)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()


def parse_solution_capsule(
    text: str,
    *,
    candidate_id: str,
    source: str,
    fallback_fingerprint: MethodFingerprint,
    requires_proof: bool,
    parent_candidate_id: str | None = None,
) -> SolutionCapsule:
    warnings: list[str] = []
    tagged_answer = extract_tag(text, "FINAL_CANDIDATE")
    answer = _compact_candidate(tagged_answer) if tagged_answer else extract_final_candidate(text)
    if not answer:
        warnings.append("missing_final_candidate")
        answer = ""

    tagged_final_response = extract_tag(text, "FINAL_RESPONSE")
    final_response = tagged_final_response
    if not final_response:
        warnings.append("missing_final_response")
        final_response = strip_protocol_tags(text) if requires_proof else answer

    challenge_resolution = extract_tag(text, "CHALLENGE_RESOLUTION")
    fingerprint = parse_method_fingerprint(text, fallback_fingerprint)
    claims = parse_claims(text)
    if not claims:
        warnings.append("missing_claims")

    risk_flags = _parse_list_block(text, "RISK_FLAGS")
    check_hints = _parse_list_block(text, "CHECK_HINTS")

    complete = bool(answer.strip() and final_response.strip())
    truncated = tagged_answer is None or tagged_final_response is None

    return SolutionCapsule(
        candidate_id=candidate_id,
        source=source,
        answer_raw=answer.strip(),
        final_response=final_response.strip(),
        fingerprint=fingerprint,
        claims=claims,
        check_hints=check_hints,
        risk_flags=risk_flags,
        complete=complete,
        truncated=truncated,
        response_chars=len(text),
        parse_warnings=tuple(warnings),
        parent_candidate_id=parent_candidate_id,
        challenge_resolution=challenge_resolution,
    )


def _extract_tag_or_label(text: str, tag: str) -> str | None:
    tagged = extract_tag(text, tag)
    if tagged:
        return tagged
    matches = re.findall(
        rf"(?:^|\n)\s*{re.escape(tag)}\s*[:：]\s*(.+)",
        text,
        flags=re.IGNORECASE,
    )
    return matches[-1].strip() if matches else None


def parse_audit_result(text: str) -> AuditResult:
    allowed = (
        "ACCEPT_A",
        "ACCEPT_B",
        "EQUIVALENT",
        "REPAIR_A",
        "REPAIR_B",
        "UNRESOLVED",
    )
    raw_verdict = _extract_tag_or_label(text, "VERDICT")
    if raw_verdict:
        verdict_match = re.search("|".join(allowed), raw_verdict.upper())
    else:
        matches = re.findall(
            r"\b(?:ACCEPT_A|ACCEPT_B|EQUIVALENT|REPAIR_A|REPAIR_B|UNRESOLVED)\b",
            text.upper(),
        )
        verdict_match = re.search("|".join(allowed), matches[-1]) if matches else None
    verdict = verdict_match.group(0) if verdict_match else "UNRESOLVED"

    target = (_extract_tag_or_label(text, "TARGET_CANDIDATE") or "none").strip().upper()
    if target not in {"A", "B"}:
        target = None

    target_claim = (_extract_tag_or_label(text, "TARGET_CLAIM") or "none").strip()
    if target_claim.lower() == "none":
        target_claim = None

    attack_type = (_extract_tag_or_label(text, "ATTACK_TYPE") or "none").strip().lower()
    severity = (_extract_tag_or_label(text, "SEVERITY") or "none").strip().lower()
    challenge = (_extract_tag_or_label(text, "CHALLENGE") or "none").strip()
    witness = (_extract_tag_or_label(text, "WITNESS") or "none").strip()
    resolver_hint = (_extract_tag_or_label(text, "RESOLVER_HINT") or "none").strip()

    return AuditResult(
        verdict=verdict,
        target_candidate_id=target,
        target_claim_id=target_claim,
        attack_type=attack_type,
        severity=severity,
        challenge=challenge,
        witness=None if witness.lower() == "none" else witness,
        resolver_hint=None if resolver_hint.lower() == "none" else resolver_hint,
    )
