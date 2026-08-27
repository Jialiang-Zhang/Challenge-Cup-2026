import unittest

from agent.models import MethodFingerprint, SolutionCapsule, TaskContract
from agent.submission import build_submission
from agent.task_profile import analyze_task


class SubmissionPolicyTest(unittest.TestCase):
    def _contract(self, **overrides):
        values = dict(
            primary_domain="general",
            secondary_domains=(),
            problem_kind="calculation",
            answer_schema="exact_expression",
            requires_proof=False,
            requires_exact_answer=True,
            multipart_count=1,
            risk_level="low",
            verification_modes=("format_check",),
            mandatory_attacks=("completeness",),
            likely_failure_modes=("missing_case",),
            route_hint="R0",
            primary_method="direct",
            orthogonal_method="constructive",
            question_mode="calculation",
            mode_confidence=0.8,
            alternate_modes=(),
            blank_count=0,
            choice_count=None,
            answer_obligations=("explicit_final_answer",),
            ambiguity_flags=(),
        )
        values.update(overrides)
        return TaskContract(**values)

    def _capsule(self, answer="42", response="由计算可得 42。"):
        return SolutionCapsule(
            candidate_id="A",
            source="primary",
            answer_raw=answer,
            final_response=response,
            fingerprint=MethodFingerprint(paradigm="direct"),
        )

    def test_short_answer_uses_fixed_template(self):
        result = build_submission(self._capsule(), self._contract())
        self.assertEqual(result, "最终答案：42")

    def test_choice_template_normalizes_letters(self):
        contract = self._contract(
            problem_kind="choice",
            answer_schema="choice_letters",
            question_mode="choice",
            answer_obligations=("choice_letters",),
        )
        result = build_submission(self._capsule("A、C、D", "选 A、C、D。"), contract)
        self.assertEqual(result, "最终答案：A,C,D")

    def test_proof_template_keeps_proof_body(self):
        contract = self._contract(
            problem_kind="proof",
            answer_schema="proof",
            requires_proof=True,
            requires_exact_answer=False,
            question_mode="proof",
            answer_obligations=("proof_chain",),
        )
        result = build_submission(
            self._capsule("命题成立", "因为条件成立，所以结论成立。证毕。"),
            contract,
        )
        self.assertTrue(result.startswith("结论：命题成立\n\n证明过程：\n"))
        self.assertIn("证毕", result)

    def test_explicit_derivation_uses_answer_plus_derivation(self):
        result = build_submission(
            self._capsule("D_4", "取生成元 r,s，并验证 r^4=s^2=1 与 srs=r^{-1}。"),
            self._contract(),
            explicit_requirements=("要求写出生成自同构并验证其关系",),
        )
        self.assertTrue(result.startswith("最终答案：D_4\n\n推导概要：\n"))
        self.assertIn("验证", result)

    def test_inline_options_are_detected(self):
        profile = analyze_task("选择所有正确选项：A. 甲 B. 乙 C. 丙 D. 丁")
        self.assertEqual(profile.mode, "choice")
        self.assertIn("choice_letters", profile.obligations)

    def test_derivation_obligation_is_detected(self):
        profile = analyze_task("求分裂域与Galois群，并验证两个生成自同构的关系。")
        self.assertIn("derivation_chain", profile.obligations)


if __name__ == "__main__":
    unittest.main()
