import unittest

from agent.models import TaskContract
from agent.prompt_overrides import _problem_guardrails, primary_prompt_v2


class PromptGuardrailTest(unittest.TestCase):
    @staticmethod
    def _contract(*, proof: bool = False) -> TaskContract:
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
            primary_method="theorem",
            orthogonal_method="constructive",
            question_mode="open_response",
            answer_obligations=("proof_chain",) if proof else ("derivation_chain",),
        )

    def test_shearer_guardrail_compiles_ordered_prefix_obligation(self):
        problem = (
            "先证明Shearer熵不等式，并要求明确使用“条件越多，条件熵越小”，"
            "再推出目标不等式。"
        )
        guard = _problem_guardrails(problem)
        self.assertIn("Fix one global coordinate order", guard)
        self.assertIn("SUBSET of the full prefix", guard)
        self.assertIn("Do NOT claim H(Z) <= H(Z_{-i})", guard)

    def test_distribution_density_guardrail_requires_both_formulas(self):
        problem = "严格推导随机变量的分布函数，并给出其密度。"
        guard = _problem_guardrails(problem)
        self.assertIn("distribution function and a density", guard)
        self.assertIn("BOTH requested formulas", guard)

    def test_protocol_forbids_dangling_final_candidate(self):
        prompt = primary_prompt_v2("求分布函数与密度。", self._contract())
        self.assertIn("self-contained machine-judged answer", prompt)
        self.assertIn("NEVER end FINAL_CANDIDATE", prompt)
        self.assertIn("every requested output object", prompt)


if __name__ == "__main__":
    unittest.main()
