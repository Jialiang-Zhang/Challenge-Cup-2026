import unittest

from agent.models import MethodFingerprint, SolutionCapsule
from agent.protocol_validation import is_protocol_placeholder, sanitize_solution_capsule


class ProtocolValidationTest(unittest.TestCase):
    def test_detects_instruction_placeholders(self) -> None:
        self.assertTrue(is_protocol_placeholder("Exact independent answer."))
        self.assertTrue(is_protocol_placeholder("..."))
        self.assertFalse(is_protocol_placeholder(r"-\frac{1}{8}"))

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


if __name__ == "__main__":
    unittest.main()
