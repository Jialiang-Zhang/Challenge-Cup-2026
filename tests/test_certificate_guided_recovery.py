import unittest

from agent.models import CaseState, EvidenceRecord, MethodFingerprint, SolutionCapsule, TaskContract
from agent.verified_engine import VerifiedHORAEngine


class CertificateGuidedRecoveryTest(unittest.TestCase):
    @staticmethod
    def _contract() -> TaskContract:
        return TaskContract(
            primary_domain="numerical_analysis",
            secondary_domains=(),
            problem_kind="proof",
            answer_schema="proof",
            requires_proof=True,
            requires_exact_answer=False,
            multipart_count=1,
            risk_level="high",
            verification_modes=("format_check",),
            mandatory_attacks=("transformation",),
            likely_failure_modes=("coefficient_error",),
            route_hint="R2",
            primary_method="direct",
            orthogonal_method="constructive",
            question_mode="proof",
        )

    def test_derivation_failure_becomes_safe_local_repair_challenge(self):
        state = CaseState(contract=self._contract())
        capsule = SolutionCapsule(
            candidate_id="R",
            source="rescue",
            answer_raw="sensitive-answer-must-not-leak",
            final_response="some proof",
            fingerprint=MethodFingerprint(paradigm="direct"),
            complete=True,
            truncated=False,
            protocol_complete=True,
        )
        state.add_candidate(capsule)
        state.add_evidence(
            EvidenceRecord(
                evidence_id="E1",
                candidate_id="R",
                evidence_type="derivation_certificate:bdf2_taylor_substitution_consistency",
                status="fail",
                strength="hard",
                checker="test",
                detail_code="h2_over_2_lost_during_substitution",
            )
        )

        audit = VerifiedHORAEngine._certificate_feedback_audit(state, capsule)
        self.assertIsNotNone(audit)
        self.assertEqual(audit.target_candidate_id, "R")
        self.assertEqual(audit.verdict, "REPAIR_A")
        self.assertEqual(audit.attack_type, "transformation")
        combined = " ".join(
            str(value or "")
            for value in (audit.challenge, audit.witness, audit.resolver_hint)
        )
        self.assertIn("bdf2_taylor_substitution_consistency", combined)
        self.assertIn("h2_over_2_lost_during_substitution", combined)
        self.assertNotIn("sensitive-answer-must-not-leak", combined)

    def test_requirement_failure_prefers_completeness_attack(self):
        state = CaseState(contract=self._contract())
        capsule = SolutionCapsule(
            candidate_id="R",
            source="rescue",
            answer_raw="x",
            final_response="proof",
            fingerprint=MethodFingerprint(paradigm="direct"),
            complete=True,
            truncated=False,
            protocol_complete=True,
        )
        state.add_candidate(capsule)
        state.add_evidence(
            EvidenceRecord(
                evidence_id="E2",
                candidate_id="R",
                evidence_type="explicit_requirement:generator_relations",
                status="fail",
                strength="hard",
                checker="test",
                detail_code="relation_signals=0",
            )
        )
        audit = VerifiedHORAEngine._certificate_feedback_audit(state, capsule)
        self.assertIsNotNone(audit)
        self.assertEqual(audit.attack_type, "completeness")


if __name__ == "__main__":
    unittest.main()
