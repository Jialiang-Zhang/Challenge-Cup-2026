from __future__ import annotations

import re

from .derivation_certificates import evaluate_decisive_derivation_certificates
from .evidence import challenge_from_audit, evidence_for_candidate
from .models import AuditResult, CaseState, EvidenceRecord, SolutionCapsule
from .parsing import parse_audit_result
from .resilient_engine import ResilientHORAEngine, _REQUIREMENTS
from .verification_prompts import decisive_confirmation_prompt


_REVISION_PATTERNS: tuple[tuple[str, str], ...] = (
    ("more_accurately", r"更准确地|更严格地|more accurately|more precisely"),
    ("actually", r"实际上|事实上|actually|in fact"),
    ("instead", r"改为|我们改用|instead|replace this with"),
    ("standard_restart", r"标准(?:论证|证明)(?:如下|是)|经典(?:论证|证明)(?:如下|是)|standard (?:argument|proof)"),
    ("does_not_directly", r"不直接(?:给出|得到|使用)|不能直接|does not directly|cannot directly"),
    ("correction", r"前(?:面|述).{0,40}(?:错误|不成立|不准确)|修正(?:为|如下)|correction|the previous .* (?:was|is) (?:wrong|incorrect)"),
)


def proof_revision_markers(text: str) -> tuple[str, ...]:
    """Return distinct signs that a submitted proof visibly restarts/corrects itself."""

    value = str(text or "")
    found = [
        code
        for code, pattern in _REVISION_PATTERNS
        if re.search(pattern, value, flags=re.IGNORECASE | re.DOTALL)
    ]
    return tuple(found)


def _meaningful(value: str | None) -> bool:
    text = str(value or "").strip()
    return bool(text) and text.lower() not in {"none", "null", "n/a", "unknown"}


class VerifiedHORAEngine(ResilientHORAEngine):
    """Resilient HORA with deterministic certificates and bounded local confirmation."""

    @staticmethod
    def _reasoning_heavy(state: CaseState) -> bool:
        contract = state.contract
        return (
            contract.requires_proof
            or contract.answer_schema == "proof"
            or contract.multipart_count > 1
            or "derivation_chain" in contract.answer_obligations
        )

    @staticmethod
    def _has_independent_support(state: CaseState, candidate_id: str) -> bool:
        return any(
            item.candidate_id == candidate_id
            and item.status == "pass"
            and item.strength == "independent"
            for item in evidence_for_candidate(state, candidate_id)
        )

    def _apply_candidate_evidence(self, state: CaseState, capsule: SolutionCapsule) -> None:
        super()._apply_candidate_evidence(state, capsule)

        for index, certificate in enumerate(
            evaluate_decisive_derivation_certificates(
                answer_raw=capsule.answer_raw,
                response=capsule.final_response,
                requirements=_REQUIREMENTS.get(),
            ),
            start=1,
        ):
            state.add_evidence(
                EvidenceRecord(
                    evidence_id=f"E-cert-{capsule.candidate_id}-{index}-{len(state.evidence)}",
                    candidate_id=capsule.candidate_id,
                    evidence_type=f"derivation_certificate:{certificate.code}",
                    status=certificate.status,  # type: ignore[arg-type]
                    strength="hard" if certificate.hard_failure else "structural",
                    checker="deterministic_derivation_certificate",
                    detail_code=certificate.detail,
                )
            )
            if certificate.hard_failure and certificate.status == "fail":
                state.candidates[capsule.candidate_id].eligible = False

        if not self._reasoning_heavy(state):
            return

        markers = proof_revision_markers(capsule.final_response)
        if len(markers) < 2:
            return

        state.add_evidence(
            EvidenceRecord(
                evidence_id=f"E-proof-revision-{capsule.candidate_id}-{len(state.evidence)}",
                candidate_id=capsule.candidate_id,
                evidence_type="proof_internal_revision_conflict",
                status="fail",
                strength="hard",
                checker="proof_chain_consistency_gate",
                detail_code=f"revision_markers={len(markers)}",
            )
        )
        state.candidates[capsule.candidate_id].eligible = False

    def _confirmation_result(
        self,
        *,
        problem: str,
        state: CaseState,
        guard,
        trace: list[dict],
        selected: SolutionCapsule,
    ) -> AuditResult:
        text = self._call_model(
            state=state,
            guard=guard,
            trace=trace,
            step="proof_confirmation_call",
            prompt=decisive_confirmation_prompt(
                problem,
                state.contract,
                selected,
                context_limit=self.config.max_candidate_context_chars,
            ),
            temperature=0.0,
            max_tokens=min(self.config.audit_max_tokens + 256, 1280),
            thinking_mode=False,
        )
        raw = parse_audit_result(text)

        verdict = raw.verdict
        if verdict not in {"ACCEPT_A", "REPAIR_A", "UNRESOLVED"}:
            verdict = "UNRESOLVED"
        if verdict == "ACCEPT_A" and not _meaningful(raw.witness):
            verdict = "UNRESOLVED"
        if verdict == "REPAIR_A" and not self._attack_is_concrete(raw):
            verdict = "UNRESOLVED"

        trace.append(
            {
                "step": "proof_confirmation_result",
                "content": {
                    "candidate_id": selected.candidate_id,
                    "verdict": verdict,
                    "attack_type": raw.attack_type,
                    "severity": raw.severity,
                },
            }
        )

        if verdict == "ACCEPT_A":
            state.add_evidence(
                EvidenceRecord(
                    evidence_id=f"E-confirm-{selected.candidate_id}-{len(state.evidence)}",
                    candidate_id=selected.candidate_id,
                    evidence_type="decisive_confirmation",
                    status="pass",
                    strength="semantic",
                    checker="decisive_local_verifier",
                    target_claim_id=raw.target_claim_id,
                    detail_code="independent_local_recomputation_passed",
                )
            )
            return AuditResult(
                verdict="ACCEPT_A",
                target_candidate_id=selected.candidate_id,
                target_claim_id=raw.target_claim_id,
                attack_type=raw.attack_type,
                severity=raw.severity,
                challenge=raw.challenge,
                witness=raw.witness,
                resolver_hint=raw.resolver_hint,
            )

        if verdict == "REPAIR_A":
            state.add_challenge(
                challenge_from_audit(
                    challenge_id=f"CH{len(state.challenges) + 1}",
                    candidate_id=selected.candidate_id,
                    target_claim_id=raw.target_claim_id,
                    attack_type=raw.attack_type,
                    severity=raw.severity if raw.severity in {"fatal", "major"} else "major",
                    statement=raw.challenge,
                    witness=raw.witness,
                    resolver_hint=raw.resolver_hint,
                    sustained=True,
                )
            )
            state.candidates[selected.candidate_id].eligible = False
            return AuditResult(
                verdict="REPAIR_A",
                target_candidate_id=selected.candidate_id,
                target_claim_id=raw.target_claim_id,
                attack_type=raw.attack_type,
                severity=raw.severity if raw.severity in {"fatal", "major"} else "major",
                challenge=raw.challenge,
                witness=raw.witness,
                resolver_hint=raw.resolver_hint,
            )

        return AuditResult(
            verdict="UNRESOLVED",
            target_candidate_id=selected.candidate_id,
            target_claim_id=raw.target_claim_id,
            attack_type=raw.attack_type,
            severity="minor",
            challenge=raw.challenge,
            witness=raw.witness,
            resolver_hint=raw.resolver_hint,
        )

    def _run_audit(
        self,
        problem: str,
        state: CaseState,
        guard,
        trace: list[dict],
        candidate_a: SolutionCapsule,
        candidate_b: SolutionCapsule | None,
    ) -> AuditResult:
        evidence_start = len(state.evidence)
        result = super()._run_audit(
            problem,
            state,
            guard,
            trace,
            candidate_a,
            candidate_b,
        )

        if not self._reasoning_heavy(state):
            return result
        if result.verdict not in {"ACCEPT_A", "ACCEPT_B", "EQUIVALENT"}:
            return result

        selected: SolutionCapsule | None = None
        if result.verdict == "ACCEPT_A":
            selected = candidate_a
        elif result.verdict == "ACCEPT_B":
            selected = candidate_b
        elif result.verdict == "EQUIVALENT":
            if self._has_independent_support(state, candidate_a.candidate_id):
                return result
            selected = candidate_a

        if selected is None:
            return result
        if self._has_independent_support(state, selected.candidate_id):
            return result
        if not guard.allow_model_call(state):
            return result

        confirmation = self._confirmation_result(
            problem=problem,
            state=state,
            guard=guard,
            trace=trace,
            selected=selected,
        )
        if confirmation.verdict == "ACCEPT_A":
            return result

        self._remove_new_soft_acceptance(state, evidence_start)
        if confirmation.verdict == "REPAIR_A":
            return confirmation
        return AuditResult(
            verdict="UNRESOLVED",
            target_candidate_id=selected.candidate_id,
            target_claim_id=confirmation.target_claim_id,
            attack_type=confirmation.attack_type,
            severity=confirmation.severity,
            challenge=confirmation.challenge,
            witness=confirmation.witness,
            resolver_hint=confirmation.resolver_hint,
        )
