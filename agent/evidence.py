from __future__ import annotations

import itertools

from .canonicalize import answer_appears_in_response, compare_answers, numeric_value
from .models import (
    CaseState,
    Challenge,
    EvidenceRecord,
    SolutionCapsule,
    TaskContract,
)
from .orthogonality import is_independent_support


_counter = itertools.count(1)


def _evidence_id(prefix: str = "E") -> str:
    return f"{prefix}{next(_counter)}"


def evaluate_candidate(
    capsule: SolutionCapsule,
    contract: TaskContract,
) -> list[EvidenceRecord]:
    records: list[EvidenceRecord] = []

    format_ok = bool(capsule.answer_raw.strip() and capsule.final_response.strip())
    records.append(
        EvidenceRecord(
            evidence_id=_evidence_id(),
            candidate_id=capsule.candidate_id,
            evidence_type="format_contract",
            status="pass" if format_ok else "fail",
            strength="hard" if not format_ok else "structural",
            checker="capsule_parser",
            detail_code=None if format_ok else "empty_answer_or_response",
        )
    )

    if capsule.truncated:
        records.append(
            EvidenceRecord(
                evidence_id=_evidence_id(),
                candidate_id=capsule.candidate_id,
                evidence_type="truncation",
                status="fail",
                strength="major",
                checker="capsule_parser",
                detail_code="unclosed_protocol_tag",
            )
        )

    response_consistent = answer_appears_in_response(
        capsule.answer_raw, capsule.final_response
    )
    records.append(
        EvidenceRecord(
            evidence_id=_evidence_id(),
            candidate_id=capsule.candidate_id,
            evidence_type="answer_response_consistency",
            status="pass" if response_consistent else "unknown",
            strength="structural",
            checker="answer_normalizer",
            detail_code=None if response_consistent else "candidate_not_located_in_response",
        )
    )

    if contract.primary_domain in {"probability_statistics", "random_process"}:
        numeric = numeric_value(capsule.answer_raw)
        if numeric is not None:
            in_range = -1e-12 <= numeric <= 1.0 + 1e-12
            if contract.problem_kind == "calculation" and contract.answer_schema != "integer":
                records.append(
                    EvidenceRecord(
                        evidence_id=_evidence_id(),
                        candidate_id=capsule.candidate_id,
                        evidence_type="probability_range",
                        status="pass" if in_range else "unknown",
                        strength="weak",
                        checker="numeric_range",
                        detail_code=None if in_range else "outside_unit_interval_possible_nonprobability",
                    )
                )

    if contract.multipart_count > 1:
        markers = sum(
            capsule.final_response.count(token)
            for token in ("(1)", "（1）", "①", "(a)", "(A)")
        )
        records.append(
            EvidenceRecord(
                evidence_id=_evidence_id(),
                candidate_id=capsule.candidate_id,
                evidence_type="multipart_completeness",
                status="pass" if markers or len(capsule.claims) >= contract.multipart_count else "unknown",
                strength="structural",
                checker="multipart_checker",
                detail_code=None if markers else "multipart_markers_not_confirmed",
            )
        )

    return records


def add_equivalence_evidence(
    state: CaseState,
    candidate_a: SolutionCapsule,
    candidate_b: SolutionCapsule,
    orthogonality_level: str,
) -> str:
    relation = compare_answers(candidate_a.answer_raw, candidate_b.answer_raw)
    status = "pass" if relation == "equivalent" else (
        "fail" if relation == "not_equivalent" else "unknown"
    )
    strength = (
        "independent"
        if relation == "equivalent" and is_independent_support(orthogonality_level)
        else "structural"
    )
    for candidate in (candidate_a, candidate_b):
        state.add_evidence(
            EvidenceRecord(
                evidence_id=_evidence_id(),
                candidate_id=candidate.candidate_id,
                evidence_type="cross_candidate_equivalence",
                status=status,
                strength=strength,
                checker="mathematical_equivalence",
                detail_code=f"relation={relation};orthogonality={orthogonality_level}",
            )
        )
    return relation


def challenge_from_audit(
    *,
    challenge_id: str,
    candidate_id: str | None,
    target_claim_id: str | None,
    attack_type: str,
    severity: str,
    statement: str,
    witness: str | None,
    resolver_hint: str | None,
    sustained: bool,
) -> Challenge:
    return Challenge(
        challenge_id=challenge_id,
        candidate_id=candidate_id,
        target_claim_id=target_claim_id,
        attack_type=attack_type,
        severity=severity,
        statement=statement,
        witness=witness,
        resolver_hint=resolver_hint,
        status="sustained" if sustained else "rebutted",
    )


def evidence_for_candidate(state: CaseState, candidate_id: str) -> list[EvidenceRecord]:
    return [record for record in state.evidence if record.candidate_id == candidate_id]


def challenges_for_candidate(state: CaseState, candidate_id: str) -> list[Challenge]:
    return [
        challenge for challenge in state.challenges if challenge.candidate_id == candidate_id
    ]


def has_hard_fail(state: CaseState, candidate_id: str) -> bool:
    for evidence in evidence_for_candidate(state, candidate_id):
        if evidence.status == "fail" and evidence.strength in {"hard", "fatal"}:
            return True
    for challenge in challenges_for_candidate(state, candidate_id):
        if challenge.status == "sustained" and challenge.severity == "fatal":
            return True
    return False


def has_attack_survival(state: CaseState, candidate_id: str) -> bool:
    return any(
        challenge.status in {"rebutted", "resolved_by_tool"}
        for challenge in challenges_for_candidate(state, candidate_id)
    )


def add_audit_acceptance(state: CaseState, candidate_id: str, verdict: str) -> None:
    state.add_evidence(
        EvidenceRecord(
            evidence_id=_evidence_id(),
            candidate_id=candidate_id,
            evidence_type="red_team_adjudication",
            status="pass",
            strength="semantic",
            checker="red_team_auditor",
            detail_code=verdict,
        )
    )
