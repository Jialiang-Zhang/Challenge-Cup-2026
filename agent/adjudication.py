from __future__ import annotations

from .evidence import (
    challenges_for_candidate,
    evidence_for_candidate,
    has_attack_survival,
    has_hard_fail,
)
from .models import CaseState, CandidateRecord


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


def select_best_candidate(state: CaseState) -> CandidateRecord | None:
    eligible = [
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
    if not eligible:
        return None
    return max(eligible, key=lambda record: _candidate_key(state, record))


def freeze_candidate(state: CaseState, candidate_id: str) -> None:
    record = state.candidates[candidate_id]
    if has_hard_fail(state, candidate_id) or record.capsule.truncated:
        raise ValueError("cannot freeze a hard-failed or truncated candidate")
    record.frozen = True
    state.committed_candidate_id = candidate_id
