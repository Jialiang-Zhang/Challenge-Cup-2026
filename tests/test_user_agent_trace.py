import json
import unittest

from user_agent import AgentConfig, ReasoningAgent


PRIMARY_NUMERIC = r"""
<FINAL_CANDIDATE>-1/8</FINAL_CANDIDATE>
<METHOD_FINGERPRINT>
paradigm: theorem
representation: symbolic
theorem_family: residue formula
tool_channel: none
interpretation_id: I1
exposed_to_primary: false
</METHOD_FINGERPRINT>
<CRITICAL_CLAIMS><CLAIM id="C1">The pole is simple.</CLAIM></CRITICAL_CLAIMS>
<CHECK_HINTS>direct limit</CHECK_HINTS>
<RISK_FLAGS>none</RISK_FLAGS>
<FINAL_RESPONSE>-1/8</FINAL_RESPONSE>
"""

BLIND_NUMERIC = r"""
<FINAL_CANDIDATE>-\frac{1}{8}</FINAL_CANDIDATE>
<METHOD_FINGERPRINT>
paradigm: constructive
representation: coordinate
theorem_family: direct Laurent coefficient
tool_channel: sympy
interpretation_id: I1
exposed_to_primary: false
</METHOD_FINGERPRINT>
<CRITICAL_CLAIMS><CLAIM id="C1">Directly isolate the coefficient.</CLAIM></CRITICAL_CLAIMS>
<CHECK_HINTS>series expansion</CHECK_HINTS>
<RISK_FLAGS>none</RISK_FLAGS>
<FINAL_RESPONSE>-\frac{1}{8}</FINAL_RESPONSE>
"""

AUDIT_ACCEPT_A = """
<VERDICT>ACCEPT_A</VERDICT>
<TARGET_CANDIDATE>A</TARGET_CANDIDATE>
<TARGET_CLAIM>none</TARGET_CLAIM>
<ATTACK_TYPE>boundary</ATTACK_TYPE>
<SEVERITY>none</SEVERITY>
<CHALLENGE>none</CHALLENGE>
<WITNESS>none</WITNESS>
<RESOLVER_HINT>none</RESOLVER_HINT>
"""


class FakeClient:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def chat(self, messages, temperature=None, max_tokens=None, thinking_mode=None):
        self.calls.append(
            {
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "thinking_mode": thinking_mode,
            }
        )
        if not self.responses:
            raise AssertionError("unexpected model call")
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


class UserAgentTraceTest(unittest.TestCase):
    def test_low_risk_default_uses_primary_and_red_team_only(self) -> None:
        client = FakeClient([PRIMARY_NUMERIC, AUDIT_ACCEPT_A])
        agent = ReasoningAgent(client=client)
        result = agent.solve("求函数在简单极点处的留数。", {"idx": 6})

        self.assertEqual(result["final_response"], "最终答案：-1/8")
        self.assertEqual(len(client.calls), 2)
        self.assertIs(client.calls[0]["thinking_mode"], False)
        self.assertIs(client.calls[1]["thinking_mode"], False)
        self.assertFalse(
            any(step["step"] == "orthogonal_comparison" for step in result["trace"])
        )
        self.assertTrue(
            any(step["step"] == "red_team_result" for step in result["trace"])
        )

    def test_equivalent_orthogonal_answers_commit_in_two_calls(self) -> None:
        client = FakeClient([PRIMARY_NUMERIC, BLIND_NUMERIC])
        agent = ReasoningAgent(
            client=client,
            config=AgentConfig(always_run_blind=True),
        )
        problem = "求函数在简单极点处的留数。PRIVATE-HIDDEN-PROBLEM"

        result = agent.solve(problem, {"idx": 7})

        self.assertEqual(result["final_response"], "最终答案：-1/8")
        self.assertEqual(len(client.calls), 2)
        trace_text = json.dumps(result["trace"], ensure_ascii=False)
        self.assertNotIn(problem, trace_text)
        self.assertNotIn("-1/8", trace_text)
        self.assertNotIn("PRIVATE-HIDDEN-PROBLEM", trace_text)
        self.assertEqual(result["trace"][-1]["step"], "transaction_commit")
        comparison = [
            step for step in result["trace"] if step["step"] == "orthogonal_comparison"
        ][0]
        self.assertEqual(comparison["content"]["equivalence"], "equivalent")
        self.assertIn(comparison["content"]["orthogonality"], {"O2", "O3"})

    def test_high_risk_proof_runs_red_team(self) -> None:
        primary = r"""
<FINAL_CANDIDATE>结论成立</FINAL_CANDIDATE>
<METHOD_FINGERPRINT>
paradigm: theorem
representation: operator
theorem_family: dominated convergence
tool_channel: none
interpretation_id: I1
exposed_to_primary: false
</METHOD_FINGERPRINT>
<CRITICAL_CLAIMS><CLAIM id="C1">All DCT conditions hold.</CLAIM></CRITICAL_CLAIMS>
<FINAL_RESPONSE>由支配收敛定理，结论成立。</FINAL_RESPONSE>
"""
        blind = r"""
<FINAL_CANDIDATE>结论成立</FINAL_CANDIDATE>
<METHOD_FINGERPRINT>
paradigm: constructive
representation: symbolic
theorem_family: uniform integrability
tool_channel: none
interpretation_id: I1
exposed_to_primary: false
</METHOD_FINGERPRINT>
<CRITICAL_CLAIMS><CLAIM id="C1">Use truncation and uniform integrability.</CLAIM></CRITICAL_CLAIMS>
<FINAL_RESPONSE>从一致可积性与截断估计可得结论。</FINAL_RESPONSE>
"""
        audit = """
<VERDICT>EQUIVALENT</VERDICT>
<TARGET_CANDIDATE>none</TARGET_CANDIDATE>
<TARGET_CLAIM>none</TARGET_CLAIM>
<ATTACK_TYPE>theorem_precondition</ATTACK_TYPE>
<SEVERITY>none</SEVERITY>
<CHALLENGE>none</CHALLENGE>
<WITNESS>DCT applies because the sequence converges a.e. and is dominated by an integrable function.</WITNESS>
<RESOLVER_HINT>check domination and a.e. convergence</RESOLVER_HINT>
"""
        client = FakeClient([primary, blind, audit])
        agent = ReasoningAgent(client=client)
        result = agent.solve(
            "证明在支配收敛条件下可以交换极限与Lebesgue积分。", {"idx": 1}
        )
        self.assertEqual(len(client.calls), 3)
        self.assertIs(client.calls[0]["thinking_mode"], False)
        self.assertIs(client.calls[1]["thinking_mode"], False)
        self.assertIs(client.calls[2]["thinking_mode"], False)
        self.assertTrue(result["final_response"].startswith("结论：结论成立"))
        self.assertIn("证明过程", result["final_response"])
        self.assertTrue(
            any(step["step"] == "red_team_result" for step in result["trace"])
        )

    def test_red_team_selects_second_candidate_on_disagreement(self) -> None:
        wrong = PRIMARY_NUMERIC.replace("-1/8", "1/8")
        audit = """
<VERDICT>ACCEPT_B</VERDICT>
<TARGET_CANDIDATE>A</TARGET_CANDIDATE>
<TARGET_CLAIM>C1</TARGET_CLAIM>
<ATTACK_TYPE>transformation</ATTACK_TYPE>
<SEVERITY>fatal</SEVERITY>
<CHALLENGE>The sign is wrong.</CHALLENGE>
<WITNESS>Direct limit is negative.</WITNESS>
<RESOLVER_HINT>substitute the pole</RESOLVER_HINT>
"""
        client = FakeClient([wrong, BLIND_NUMERIC, audit])
        agent = ReasoningAgent(
            client=client,
            config=AgentConfig(always_run_blind=True),
        )
        result = agent.solve("计算该复函数在极点处的留数。", {"idx": 2})
        self.assertEqual(len(client.calls), 3)
        self.assertEqual(result["final_response"], r"最终答案：-\frac{1}{8}")

    def test_one_shot_targeted_repair(self) -> None:
        wrong_a = PRIMARY_NUMERIC.replace("-1/8", "1/8")
        wrong_b = BLIND_NUMERIC.replace(r"-\frac{1}{8}", r"\frac{3}{8}")
        audit = """
<VERDICT>REPAIR_A</VERDICT>
<TARGET_CANDIDATE>A</TARGET_CANDIDATE>
<TARGET_CLAIM>C1</TARGET_CLAIM>
<ATTACK_TYPE>transformation</ATTACK_TYPE>
<SEVERITY>fatal</SEVERITY>
<CHALLENGE>The sign was lost.</CHALLENGE>
<WITNESS>The direct limit is negative.</WITNESS>
<RESOLVER_HINT>recompute the local coefficient</RESOLVER_HINT>
"""
        repaired = r"""
<FINAL_CANDIDATE>-1/8</FINAL_CANDIDATE>
<METHOD_FINGERPRINT>
paradigm: corrected-theorem
representation: symbolic
theorem_family: residue formula
tool_channel: none
interpretation_id: I1
exposed_to_primary: true
</METHOD_FINGERPRINT>
<CRITICAL_CLAIMS>
<CLAIM id="C1">At a simple pole z0, the residue is lim_{z->z0}(z-z0)f(z).</CLAIM>
<CLAIM id="C2">Direct substitution gives the numerator -1 and denominator 8.</CLAIM>
</CRITICAL_CLAIMS>
<CHALLENGE_RESOLUTION>The sign is fixed by recomputing the simple-pole limit instead of inheriting the parent value.</CHALLENGE_RESOLUTION>
<CHECK_HINTS>substitute the pole and simplify numerator and denominator separately</CHECK_HINTS>
<RISK_FLAGS>none</RISK_FLAGS>
<FINAL_RESPONSE>
由简单极点的留数公式，若极点为 z_0，则
$$\operatorname{Res}(f,z_0)=\lim_{z\to z_0}(z-z_0)f(z).$$
因此不能从父候选直接继承符号，而要重新计算该极限。把题中分子与分母分别代入并约去唯一的一阶零因子后，分子给出 $-1$，其余非零因子的乘积为 $8$，所以
$$\operatorname{Res}(f,z_0)=\frac{-1}{8}=-\frac18.$$
因为约去的只是产生简单极点的线性因子，其余因子在 $z_0$ 处均非零，所以上述极限存在且没有额外符号变化。故修复后的留数为 $-1/8$，证毕。
</FINAL_RESPONSE>
"""
        client = FakeClient([wrong_a, wrong_b, audit, repaired])
        agent = ReasoningAgent(client=client, config=AgentConfig(max_model_calls=4))
        result = agent.solve("严格证明并计算该复函数在极点处的留数。", {"idx": 3})
        self.assertEqual(len(client.calls), 4)
        self.assertTrue(result["final_response"].startswith("结论：-1/8"))
        self.assertIn("证明过程", result["final_response"])
        self.assertEqual(result["trace"][-1]["content"]["repair_count"], 1)


if __name__ == "__main__":
    unittest.main()
