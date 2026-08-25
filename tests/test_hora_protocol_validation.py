import unittest

from agent.evidence import evaluate_candidate
from agent.models import MethodFingerprint, SolutionCapsule, TaskContract
from agent.protocol_validation import (
    is_protocol_placeholder,
    leading_response_answer,
    sanitize_solution_capsule,
)


class ProtocolValidationTest(unittest.TestCase):
    def test_detects_instruction_placeholders(self) -> None:
        self.assertTrue(is_protocol_placeholder("Exact independent answer."))
        self.assertTrue(is_protocol_placeholder("..."))
        self.assertFalse(is_protocol_placeholder(r"-\frac{1}{8}"))

    def test_leading_response_answer_preserves_negative_signs(self) -> None:
        self.assertEqual(leading_response_answer("-1\nproof"), "-1")
        self.assertEqual(
            leading_response_answer(r"-\frac{1}{8}\nproof"),
            r"-\frac{1}{8}\nproof",
        )
        self.assertIsNone(leading_response_answer("- answer\nproof"))

    def test_placeholder_candidate_is_not_eligible_as_complete_content(self) -> None:
        capsule = SolutionCapsule(
            candidate_id="B",
            source="orthogonal_blind",
            answer_raw="Exact independent answer.",
            final_response="Give a concise exact answer and independent derivation.",
            fingerprint=MethodFingerprint(paradigm="constructive"),
        )
        sanitize_solution_capsule(capsule, requires_proof=False)
        self.assertEqual(capsule.answer_raw, "")
        self.assertEqual(capsule.final_response, "")
        self.assertFalse(capsule.complete)
        self.assertIn("placeholder_final_candidate", capsule.parse_warnings)

    def test_nonproof_response_can_fall_back_to_real_answer(self) -> None:
        capsule = SolutionCapsule(
            candidate_id="B",
            source="orthogonal_blind",
            answer_raw="-1",
            final_response="...",
            fingerprint=MethodFingerprint(paradigm="constructive"),
        )
        sanitize_solution_capsule(capsule, requires_proof=False)
        self.assertEqual(capsule.final_response, "-1")
        self.assertTrue(capsule.complete)

    def test_later_final_response_reconciles_conflicting_candidate(self) -> None:
        capsule = SolutionCapsule(
            candidate_id="A",
            source="primary",
            answer_raw="-1/635",
            final_response="-1\nBy FTC and f(1)=5, the value is -1.",
            fingerprint=MethodFingerprint(paradigm="theorem"),
        )
        sanitize_solution_capsule(capsule, requires_proof=False)
        self.assertEqual(capsule.answer_raw, "-1")
        self.assertIn("candidate_response_conflict", capsule.parse_warnings)
        self.assertIn("reconciled_to_final_response", capsule.parse_warnings)

    def test_consistency_check_does_not_accept_numeric_substrings(self) -> None:
        contract = TaskContract(
            primary_domain="real_analysis",
            secondary_domains=(),
            problem_kind="calculation",
            answer_schema="exact_expression",
            requires_proof=False,
            requires_exact_answer=True,
            multipart_count=1,
            risk_level="low",
            verification_modes=("format",),
            mandatory_attacks=("boundary",),
            likely_failure_modes=(),
            route_hint="R0",
            primary_method="direct",
            orthogonal_method="definition",
        )
        capsule = SolutionCapsule(
            candidate_id="A",
            source="primary",
            answer_raw="-1",
            final_response="-1/635",
            fingerprint=MethodFingerprint(paradigm="direct"),
        )
        records = evaluate_candidate(capsule, contract)
        consistency = next(
            record
            for record in records
            if record.evidence_type == "answer_response_consistency"
        )
        self.assertEqual(consistency.status, "fail")
        self.assertEqual(consistency.strength, "hard")


if __name__ == "__main__":
    unittest.main()
