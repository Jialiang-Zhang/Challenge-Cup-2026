import unittest

from agent.evidence import evaluate_candidate, has_hard_fail
from agent.models import CaseState, MethodFingerprint, SolutionCapsule
from agent.parsing import parse_solution_capsule
from agent.routing import DOMAIN_PATTERNS, build_task_contract
from agent.task_profile import analyze_task


class AdaptiveTaskProfileTest(unittest.TestCase):
    def test_profiles_choice_count_without_forcing_unmarked_questions(self) -> None:
        choice = analyze_task(
            "选择其中两个正确选项：\nA. 命题一\nB. 命题二\nC. 命题三\nD. 命题四"
        )
        self.assertEqual(choice.mode, "choice")
        self.assertEqual(choice.choice_count, 2)
        self.assertIn("choice_count:2", choice.obligations)

        ambiguous = analyze_task("研究函数在原点附近的行为。")
        self.assertEqual(ambiguous.mode, "open_response")
        self.assertIn("weak_mode_signal", ambiguous.ambiguity_flags)

    def test_profiles_fill_multipart_and_proof_obligations(self) -> None:
        fill = analyze_task("填空：第一空____；第二空____。")
        self.assertEqual(fill.mode, "fill")
        self.assertEqual(fill.blank_count, 2)

        proof = analyze_task("(1) 证明结论成立。\n(2) 求边界情形。")
        self.assertEqual(proof.part_count, 2)
        self.assertTrue(proof.requires_proof)
        self.assertIn("multipart_count:2", proof.obligations)
        self.assertIn("proof_chain", proof.obligations)

    def test_router_exposes_exactly_eighteen_domains_and_top_two(self) -> None:
        self.assertEqual(len(DOMAIN_PATTERNS), 18)
        contract = build_task_contract(
            "对热方程使用数值迭代并分析离散格式的稳定性与边界条件。"
        )
        self.assertEqual(contract.primary_domain, "partial_differential_equations")
        self.assertIn("numerical_analysis", contract.secondary_domains)
        self.assertLessEqual(len(contract.secondary_domains), 2)


class ProtocolRecoveryTest(unittest.TestCase):
    def test_recovers_complete_untagged_calculation_with_provenance(self) -> None:
        text = (
            "代入并化简可得 x=3。再代回原式，两边都等于 7。"
            "因此最终答案：$x=3$。"
        )
        capsule = parse_solution_capsule(
            text,
            candidate_id="A",
            source="primary",
            fallback_fingerprint=MethodFingerprint(),
            requires_proof=False,
        )
        self.assertTrue(capsule.complete)
        self.assertFalse(capsule.truncated)
        self.assertFalse(capsule.protocol_complete)
        self.assertEqual(capsule.recovery_source, "label")

    def test_lone_candidate_tag_remains_a_hard_truncation(self) -> None:
        capsule = parse_solution_capsule(
            "<FINAL_CANDIDATE>72</FINAL_CANDIDATE>",
            candidate_id="A",
            source="primary",
            fallback_fingerprint=MethodFingerprint(),
            requires_proof=False,
        )
        self.assertTrue(capsule.truncated)
        self.assertIsNone(capsule.recovery_source)

    def test_recovers_complete_untagged_proof_but_not_half_sentence(self) -> None:
        proof = (
            "由连续性，正值点存在一个邻域使函数仍为正，因此该邻域上的积分严格为正。"
            "这与总积分等于零矛盾，所以函数不可能处处非负且在一点严格为正。"
            "故最终结论：函数必须恒等于零。"
        )
        good = parse_solution_capsule(
            proof,
            candidate_id="A",
            source="primary",
            fallback_fingerprint=MethodFingerprint(),
            requires_proof=True,
        )
        self.assertFalse(good.truncated)

        bad = parse_solution_capsule(
            proof[:-12] + "因此接下来需要",
            candidate_id="B",
            source="blind",
            fallback_fingerprint=MethodFingerprint(),
            requires_proof=True,
        )
        self.assertTrue(bad.truncated)


class AnswerCoverageTest(unittest.TestCase):
    def test_choice_cardinality_is_a_hard_contract(self) -> None:
        contract = build_task_contract(
            "选择其中两个正确选项：\nA. 一\nB. 二\nC. 三\nD. 四"
        )
        capsule = SolutionCapsule(
            candidate_id="A",
            source="primary",
            answer_raw="A",
            final_response="A",
            fingerprint=MethodFingerprint(),
        )
        state = CaseState(contract=contract)
        state.add_candidate(capsule)
        for record in evaluate_candidate(capsule, contract):
            state.add_evidence(record)
        self.assertTrue(has_hard_fail(state, "A"))

        complete = SolutionCapsule(
            candidate_id="B",
            source="blind",
            answer_raw="A,C",
            final_response="A,C",
            fingerprint=MethodFingerprint(),
        )
        state.add_candidate(complete)
        for record in evaluate_candidate(complete, contract):
            state.add_evidence(record)
        self.assertFalse(has_hard_fail(state, "B"))

    def test_single_blank_vector_is_not_split_on_its_comma(self) -> None:
        contract = build_task_contract("填空：所求向量为____。")
        capsule = SolutionCapsule(
            candidate_id="A",
            source="primary",
            answer_raw="(1,2)",
            final_response="(1,2)",
            fingerprint=MethodFingerprint(),
        )
        state = CaseState(contract=contract)
        state.add_candidate(capsule)
        for record in evaluate_candidate(capsule, contract):
            state.add_evidence(record)
        self.assertFalse(has_hard_fail(state, "A"))


if __name__ == "__main__":
    unittest.main()
