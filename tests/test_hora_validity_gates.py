import unittest

from agent.models import AgentConfig, MethodFingerprint, SolutionCapsule
from agent.protocol_validation import sanitize_solution_capsule
from user_agent import ReasoningAgent


PRIMARY_72 = r"""
<FINAL_CANDIDATE>72</FINAL_CANDIDATE>
<METHOD_FINGERPRINT>
paradigm: theorem
representation: symbolic
theorem_family: finite field structure
tool_channel: none
interpretation_id: I1
exposed_to_primary: false
</METHOD_FINGERPRINT>
<CRITICAL_CLAIMS><CLAIM id="C1">The unique proper subfield has 9 elements.</CLAIM></CRITICAL_CLAIMS>
<CHECK_HINTS>extension degree</CHECK_HINTS>
<RISK_FLAGS>none</RISK_FLAGS>
<FINAL_RESPONSE>72</FINAL_RESPONSE>
"""

BLIND_54 = r"""
<FINAL_CANDIDATE>54</FINAL_CANDIDATE>
<METHOD_FINGERPRINT>
paradigm: constructive
representation: coordinate
theorem_family: direct count
tool_channel: none
interpretation_id: I1
exposed_to_primary: false
</METHOD_FINGERPRINT>
<CRITICAL_CLAIMS><CLAIM id="C1">A competing count gives 54.</CLAIM></CRITICAL_CLAIMS>
<CHECK_HINTS>finite enumeration</CHECK_HINTS>
<RISK_FLAGS>none</RISK_FLAGS>
<FINAL_RESPONSE>54</FINAL_RESPONSE>
"""

BLIND_54_TRUNCATED = BLIND_54.replace("<FINAL_RESPONSE>54</FINAL_RESPONSE>", "")

AUDIT_EQUIVALENT = r"""
<VERDICT>EQUIVALENT</VERDICT>
<TARGET_CANDIDATE>none</TARGET_CANDIDATE>
<TARGET_CLAIM>none</TARGET_CLAIM>
<ATTACK_TYPE>none</ATTACK_TYPE>
<SEVERITY>none</SEVERITY>
<CHALLENGE>none</CHALLENGE>
<WITNESS>none</WITNESS>
<RESOLVER_HINT>none</RESOLVER_HINT>
"""

AUDIT_ACCEPT_B = AUDIT_EQUIVALENT.replace("EQUIVALENT", "ACCEPT_B")


def capsule(answer: str, candidate_id: str = "A") -> str:
    return f"""
<FINAL_CANDIDATE>{answer}</FINAL_CANDIDATE>
<METHOD_FINGERPRINT>
paradigm: direct
representation: symbolic
theorem_family: arithmetic
tool_channel: none
interpretation_id: I1
exposed_to_primary: false
</METHOD_FINGERPRINT>
<CRITICAL_CLAIMS><CLAIM id="C1">The arithmetic is decisive.</CLAIM></CRITICAL_CLAIMS>
<CHECK_HINTS>substitution</CHECK_HINTS>
<RISK_FLAGS>none</RISK_FLAGS>
<FINAL_RESPONSE>{answer}</FINAL_RESPONSE>
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
        return self.responses.pop(0)


class ValidityGateTest(unittest.TestCase):
    def test_red_team_cannot_select_truncated_second_candidate(self) -> None:
        client = FakeClient([PRIMARY_72, BLIND_54_TRUNCATED, AUDIT_ACCEPT_B])
        agent = ReasoningAgent(
            client=client,
            config=AgentConfig(always_run_blind=True, max_model_calls=3),
        )
        result = agent.solve("计算有限域生成元的个数。", {"idx": 0})
        self.assertEqual(result["final_response"], "72")
        red = [step for step in result["trace"] if step["step"] == "red_team_result"][-1]
        self.assertEqual(red["content"]["raw_verdict"], "ACCEPT_B")
        self.assertEqual(red["content"]["verdict"], "UNRESOLVED")
        gate = [step for step in result["trace"] if step["step"] == "candidate_gate"][-1]
        self.assertEqual(gate["content"]["invalid_candidate_ids"], ["B"])

    def test_red_team_equivalent_verdict_is_vetoed_by_local_inequality(self) -> None:
        client = FakeClient([PRIMARY_72, BLIND_54, AUDIT_EQUIVALENT])
        agent = ReasoningAgent(
            client=client,
            config=AgentConfig(always_run_blind=True, max_model_calls=3),
        )
        result = agent.solve("计算有限域生成元的个数。", {"idx": 0})
        self.assertEqual(result["final_response"], "72")
        red = [step for step in result["trace"] if step["step"] == "red_team_result"][-1]
        self.assertEqual(red["content"]["raw_verdict"], "EQUIVALENT")
        self.assertEqual(red["content"]["verdict"], "UNRESOLVED")
        self.assertEqual(red["content"]["deterministic_relation"], "not_equivalent")

    def test_repair_is_reaudited_when_budget_remains(self) -> None:
        audit_repair = r"""
<VERDICT>REPAIR_A</VERDICT>
<TARGET_CANDIDATE>A</TARGET_CANDIDATE>
<TARGET_CLAIM>C1</TARGET_CLAIM>
<ATTACK_TYPE>transformation</ATTACK_TYPE>
<SEVERITY>fatal</SEVERITY>
<CHALLENGE>The arithmetic result is incorrect.</CHALLENGE>
<WITNESS>Direct addition gives 2.</WITNESS>
<RESOLVER_HINT>Recompute 1+1.</RESOLVER_HINT>
"""
        audit_accept = r"""
<VERDICT>ACCEPT_A</VERDICT>
<TARGET_CANDIDATE>none</TARGET_CANDIDATE>
<TARGET_CLAIM>none</TARGET_CLAIM>
<ATTACK_TYPE>boundary</ATTACK_TYPE>
<SEVERITY>none</SEVERITY>
<CHALLENGE>none</CHALLENGE>
<WITNESS>none</WITNESS>
<RESOLVER_HINT>none</RESOLVER_HINT>
"""
        client = FakeClient([capsule("1"), audit_repair, capsule("2", "C"), audit_accept])
        agent = ReasoningAgent(
            client=client,
            config=AgentConfig(always_run_blind=False, max_model_calls=4),
        )
        result = agent.solve("计算 1+1。", {"idx": 9})
        self.assertEqual(result["final_response"], "2")
        self.assertEqual(len(client.calls), 4)
        red_steps = [step for step in result["trace"] if step["step"] == "red_team_result"]
        self.assertEqual(len(red_steps), 2)
        self.assertEqual(red_steps[-1]["content"]["target_candidate_id"], None)
        self.assertEqual(result["trace"][-1]["content"]["repair_count"], 1)

    def test_internal_exact_assertion_reconciles_malformed_tag(self) -> None:
        item = SolutionCapsule(
            candidate_id="C",
            source="targeted_repair",
            answer_raw="-1/12",
            final_response="The exact value is $-1$ by the fundamental theorem of calculus.",
            fingerprint=MethodFingerprint(paradigm="corrected-theorem"),
        )
        item.claims = []
        sanitize_solution_capsule(item, requires_proof=False)
        self.assertEqual(item.answer_raw, "-1")
        self.assertIn("candidate_internal_conflict", item.parse_warnings)


if __name__ == "__main__":
    unittest.main()
