from __future__ import annotations

import re

from .evidence import (
    challenges_for_candidate,
    evidence_for_candidate,
    has_attack_survival,
    has_hard_fail,
)
from .models import CaseState, CandidateRecord, EvidenceRecord


_PRESENTATION_ONLY_HARD_FAILURES = {"truncation"}
_PLACEHOLDER_RE = re.compile(
    r"^(?:exact|corrected exact|final)\s+(?:answer|value|result)\.?$|"
    r"^(?:准确|最终|正确)答案[。.]?$",
    re.IGNORECASE,
)


def _meaningful(value: str | None) -> bool:
    text = str(value or "").strip()
    return bool(text) and text.lower() not in {"none", "null", "n/a", "unknown"}


def challenge_has_concrete_basis(challenge) -> bool:
    """Whether a semantic challenge contains enough detail to veto a candidate.

    A red-team label alone is not mathematical evidence.  A veto needs a concrete
    statement plus either a witness/check, or a claim-localized mathematical attack.
    """

    if not _meaningful(getattr(challenge, "statement", None)):
        return False
    if _meaningful(getattr(challenge, "witness", None)):
        return True
    if _meaningful(getattr(challenge, "resolver_hint", None)):
        return True
    return bool(
        getattr(challenge, "target_claim_id", None)
        and str(getattr(challenge, "attack_type", "")).lower()
        in {
            "assumption",
            "theorem_precondition",
            "counterexample",
            "boundary",
            "transformation",
            "quantifier",
            "completeness",
            "numerical_stress",
        }
    )


def has_irreversible_evidence_failure(state: CaseState, candidate_id: str) -> bool:
    """Hard failures that remain disqualifying even in last-resort recovery.

    Missing XML/protocol closure is treated separately from a mathematical
    contradiction.  Empty answers, inconsistent answer/response pairs, invalid
    objective answer shapes, and concrete fatal challenges remain non-recoverable.
    """

    for item in evidence_for_candidate(state, candidate_id):
        if item.status != "fail" or item.strength not in {"hard", "fatal"}:
            continue
        if item.evidence_type in _PRESENTATION_ONLY_HARD_FAILURES:
            continue
        return True

    for challenge in challenges_for_candidate(state, candidate_id):
        if (
            challenge.status == "sustained"
            and challenge.severity in {"fatal", "major"}
            and challenge_has_concrete_basis(challenge)
        ):
            return True
    return False


def _candidate_key(state: CaseState, record: CandidateRecord) -> tuple[int, ...]:
    candidate_id = record.capsule.candidate_id
    evidence = evidence_for_candidate(state, candidate_id)
    challenges = challenges_for_candidate(state, candidate_id)

    format_pass = any(
        item.evidence_type == "format_contract" and item.status == "pass"
        for item in evidence
    )
    structural_passes = sum(
        item.status == "pass" and item.strength in {"structural", "independent", "semantic"}
        for item in evidence
    )
    independent_support = any(
        item.strength == "independent" and item.status == "pass" for item in evidence
    )
    semantic_accept = any(
        item.evidence_type == "red_team_adjudication" and item.status == "pass"
        for item in evidence
    )
    unresolved_fatal = sum(
        challenge.status == "sustained" and challenge.severity == "fatal"
        for challenge in challenges
    )
    unresolved_total = sum(challenge.status == "open" for challenge in challenges)
    stable_primary = record.capsule.source == "primary" and record.capsule.parent_candidate_id is None

    return (
        int(record.eligible),
        int(format_pass),
        int(not has_hard_fail(state, candidate_id)),
        int(has_attack_survival(state, candidate_id)),
        int(semantic_accept),
        int(independent_support),
        structural_passes,
        int(record.capsule.complete and not record.capsule.truncated),
        -unresolved_fatal,
        -unresolved_total,
        int(stable_primary),
        -record.capsule.response_chars,
    )


def _proof_recovery_is_credible(state: CaseState, record: CandidateRecord) -> bool:
    response = record.capsule.final_response.strip()
    if not response:
        return False
    minimum = 80 if re.search(r"[\u4e00-\u9fff]", response) else 150
    if len(response) < minimum:
        return False
    signals = re.findall(
        r"(?:because|since|therefore|hence|by\s+|contradiction|"
        r"因为|由于|根据|所以|因此|故|从而|矛盾|得证)",
        response,
        flags=re.IGNORECASE,
    )
    return bool(signals) or len(record.capsule.claims) >= 2


def _is_safe_fallback_candidate(state: CaseState, record: CandidateRecord) -> bool:
    capsule = record.capsule
    answer = capsule.answer_raw.strip()
    response = capsule.final_response.strip()
    if not answer or not response or _PLACEHOLDER_RE.fullmatch(answer):
        return False
    if not capsule.complete:
        return False
    if has_irreversible_evidence_failure(state, capsule.candidate_id):
        return False

    contract = state.contract
    if contract.requires_proof or contract.answer_schema == "proof":
        return _proof_recovery_is_credible(state, record)

    # For objective/fill/calculation tasks a usable answer can survive a broken
    # envelope; the final submission layer will normalize the answer shape.
    return True


def _fallback_key(state: CaseState, record: CandidateRecord) -> tuple[int, ...]:
    evidence = evidence_for_candidate(state, record.capsule.candidate_id)
    pass_count = sum(item.status == "pass" for item in evidence)
    independent = sum(
        item.status == "pass" and item.strength == "independent" for item in evidence
    )
    semantic = sum(
        item.status == "pass" and item.strength == "semantic" for item in evidence
    )
    source_priority = {
        "targeted_repair": 4,
        "rescue": 3,
        "orthogonal_blind": 2,
        "primary": 1,
    }.get(record.capsule.source, 0)
    return (
        int(not record.capsule.truncated),
        int(record.capsule.protocol_complete),
        independent,
        semantic,
        pass_count,
        source_priority,
        -record.capsule.response_chars,
    )


def select_best_candidate(state: CaseState) -> CandidateRecord | None:
    strict = [
        record
        for record in state.candidates.values()
        if (
            record.eligible
            and record.capsule.answer_raw.strip()
            and record.capsule.complete
            and not record.capsule.truncated
            and not has_hard_fail(state, record.capsule.candidate_id)
        )
    ]
    if strict:
        return max(strict, key=lambda record: _candidate_key(state, record))

    # Preserve the normal rescue attempt.  Degraded commitment is only enabled
    # after a rescue candidate has actually been produced, i.e. after the strict
    # route has already exhausted its recovery opportunity.
    if not any(record.capsule.source == "rescue" for record in state.candidates.values()):
        return None

    fallback = [
        record for record in state.candidates.values() if _is_safe_fallback_candidate(state, record)
    ]
    if not fallback:
        return None

    winner = max(fallback, key=lambda record: _fallback_key(state, record))
    winner.eligible = True
    evidence_id = f"E-fallback-{winner.capsule.candidate_id}"
    if not any(item.evidence_id == evidence_id for item in state.evidence):
        state.add_evidence(
            EvidenceRecord(
                evidence_id=evidence_id,
                candidate_id=winner.capsule.candidate_id,
                evidence_type="safe_fallback_commit",
                status="pass",
                strength="structural",
                checker="degraded_commit_gate",
                detail_code="strict_pool_empty_after_rescue",
            )
        )
    return winner


def freeze_candidate(state: CaseState, candidate_id: str) -> None:
    record = state.candidates[candidate_id]
    strict_ok = not has_hard_fail(state, candidate_id) and not record.capsule.truncated
    if not strict_ok and not _is_safe_fallback_candidate(state, record):
        raise ValueError("cannot freeze a mathematically unsafe candidate")
    record.frozen = True
    state.committed_candidate_id = candidate_id
