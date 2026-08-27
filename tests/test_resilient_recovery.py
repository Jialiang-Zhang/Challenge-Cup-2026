import unittest

from agent.adjudication import freeze_candidate, select_best_candidate
from agent.models import (
    AuditResult,
    CaseState,
    EvidenceRecord,
    MethodFingerprint,
    SolutionCapsule,
    TaskContract,
)
from agent.resilient_engine import ResilientHORAEngine, extract_explicit_requirements


class ResilientRecoveryTest(unittest.TestCase):
    def _contract(self, *, proof=False, mode="open_response"):
        return TaskContract(
            primary_domain="general",
            secondary_domains=(),
            problem_kind="proof" if proof else "calculation",
            answer_schema="proof" if proof else "exact_expression",
            requires_proof=proof,
            requires_exact_answer=not proof,
            multipart_count=1,
            risk_level="high" if proof else "medium",
            verification_modes=("format_check",),
            mandatory_attacks=("completeness",),
            likely_failure_modes=("missing_case",),
            route_hint="R2" if proof else "R1",
            primary_method="direct",
            orthogonal_method="constructive",
            question_mode=mode,
        )

    @staticmethod
    def _capsule(candidate_id="A", source="primary", *, proof=False, truncated=True):
        response = (
            "由已知条件先得到关键等式。因为每一步都保持等价，所以可推出目标结论。"
            "再检查边界条件与定义域均满足，因此结论成立，证毕。"
            if proof
            else "42"
        )
        return SolutionCapsule(
            candidate_id=candidate_id,
            source=source,
            answer_raw="42",
            final_response=response,
            fingerprint=MethodFingerprint(paradigm="direct"),
            complete=True,
            truncated=truncated,
            protocol_complete=not truncated,
        )

    def _add_presentation_failure(self, state, capsule):
        state.add_candidate(capsule)
        state.add_evidence(
            EvidenceRecord(
                evidence_id=f"fmt-{capsule.candidate_id}",
                candidate_id=capsule.candidate_id,
                evidence_type="format_contract",
                status="pass",
                strength="structural",
                checker="test",
            )
        )
        state.add_evidence(
            EvidenceRecord(
                evidence_id=f"trunc-{capsule.candidate_id}",
                candidate_id=capsule.candidate_id,
                evidence_type="truncation",
                status="fail",
                strength="hard",
                checker="test",
            )
        )

    def test_degraded_commit_waits_until_rescue_exists(self):
        state = CaseState(contract=self._contract())
        self._add_presentation_failure(state, self._capsule())
        self.assertIsNone(select_best_candidate(state))

        self._add_presentation_failure(
            state,
            self._capsule(candidate_id="R", source="rescue"),
        )
        winner = select_best_candidate(state)
        self.assertIsNotNone(winner)
        self.assertEqual(winner.capsule.answer_raw, "42")
        freeze_candidate(state, winner.capsule.candidate_id)
        self.assertTrue(winner.frozen)

    def test_degraded_commit_rejects_mathematical_hard_failure(self):
        state = CaseState(contract=self._contract())
        rescue = self._capsule(candidate_id="R", source="rescue")
        self._add_presentation_failure(state, rescue)
        state.add_evidence(
            EvidenceRecord(
                evidence_id="bad-consistency",
                candidate_id="R",
                evidence_type="answer_response_consistency",
                status="fail",
                strength="hard",
                checker="test",
            )
        )
        self.assertIsNone(select_best_candidate(state))

    def test_proof_fallback_requires_a_real_chain(self):
        state = CaseState(contract=self._contract(proof=True))
        weak = self._capsule(candidate_id="R", source="rescue", proof=True)
        weak.final_response = "结论成立。"
        self._add_presentation_failure(state, weak)
        self.assertIsNone(select_best_candidate(state))

    def test_requirement_extraction_keeps_explicit_obligations(self):
        problem = (
            "证明结论成立。要求：(1) 验证边界条件；(2) 说明为什么该变换可逆；"
            "进一步证明解的唯一性。"
        )
        requirements = extract_explicit_requirements(problem)
        joined = " | ".join(requirements)
        self.assertIn("验证边界条件", joined)
        self.assertIn("变换可逆", joined)
        self.assertIn("唯一性", joined)

    def test_soft_fatal_label_without_basis_is_not_concrete(self):
        audit = AuditResult(
            verdict="REPAIR_A",
            target_candidate_id="A",
            target_claim_id=None,
            attack_type="none",
            severity="fatal",
            challenge="looks suspicious",
            witness=None,
            resolver_hint=None,
        )
        self.assertFalse(ResilientHORAEngine._attack_is_concrete(audit))

    def test_claim_localized_precondition_attack_is_concrete(self):
        audit = AuditResult(
            verdict="REPAIR_A",
            target_candidate_id="A",
            target_claim_id="C2",
            attack_type="theorem_precondition",
            severity="fatal",
            challenge="The theorem requires compactness, which was not established.",
            witness=None,
            resolver_hint=None,
        )
        self.assertTrue(ResilientHORAEngine._attack_is_concrete(audit))


if __name__ == "__main__":
    unittest.main()
