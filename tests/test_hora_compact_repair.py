import unittest

from user_agent import AgentConfig, ReasoningAgent


PRIMARY_WRONG = r"""
<FINAL_CANDIDATE>-1/635</FINAL_CANDIDATE>
<METHOD_FINGERPRINT>
paradigm: theorem
representation: symbolic
theorem_family: fundamental theorem of calculus
tool_channel: none
interpretation_id: I1
exposed_to_primary: false
</METHOD_FINGERPRINT>
<CRITICAL_CLAIMS>
<CLAIM id="C1">FTC gives F'(5)=-f_inv(5).</CLAIM>
<CLAIM id="C2">f(1)=5, so f_inv(5)=1.</CLAIM>
</CRITICAL_CLAIMS>
<FINAL_RESPONSE>-1/635</FINAL_RESPONSE>
"""

AUDIT_REPAIR = r"""
<VERDICT>REPAIR_A</VERDICT>
<TARGET_CANDIDATE>A</TARGET_CANDIDATE>
<TARGET_CLAIM>FINAL</TARGET_CLAIM>
<ATTACK_TYPE>transformation</ATTACK_TYPE>
<SEVERITY>fatal</SEVERITY>
<CHALLENGE>The submitted value contradicts the candidate's own FTC computation.</CHALLENGE>
<WITNESS>f(1)=5, hence F'(5)=-f_inv(5)=-1.</WITNESS>
<RESOLVER_HINT>Substitute x=1 and apply FTC.</RESOLVER_HINT>
"""

REPAIRED = r"""
<FINAL_CANDIDATE>-1</FINAL_CANDIDATE>
<METHOD_FINGERPRINT>
paradigm: corrected-theorem
representation: symbolic
theorem_family: fundamental theorem of calculus
tool_channel: none
interpretation_id: I1
exposed_to_primary: true
</METHOD_FINGERPRINT>
<CRITICAL_CLAIMS>
<CLAIM id="C1">F'(x)=-f_inv(x).</CLAIM>
<CLAIM id="C2">f(1)=5, hence f_inv(5)=1.</CLAIM>
</CRITICAL_CLAIMS>
<CHALLENGE_RESOLUTION>The corrected value follows directly from FTC and f(1)=5.</CHALLENGE_RESOLUTION>
<CHECK_HINTS>Substitute 1 into f.</CHECK_HINTS>
<RISK_FLAGS>none</RISK_FLAGS>
<FINAL_RESPONSE>-1</FINAL_RESPONSE>
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
        return self.responses.pop(0)


class CompactRepairTest(unittest.TestCase):
    def test_repair_uses_non_thinking_protocol_and_commits_corrected_answer(self) -> None:
        client = FakeClient([PRIMARY_WRONG, AUDIT_REPAIR, REPAIRED])
        agent = ReasoningAgent(
            client=client,
            config=AgentConfig(always_run_blind=False, max_model_calls=4),
        )
        result = agent.solve(
            "Let f_inv be the inverse of f(x)=x^7+x^5+3 and F(x)=int_x^-17 f_inv(t)dt. Find F'(5).",
            {"idx": 1},
        )
        self.assertEqual(result["final_response"], "-1")
        self.assertEqual(len(client.calls), 3)
        self.assertIs(client.calls[2]["thinking_mode"], False)
        self.assertEqual(result["trace"][-1]["content"]["repair_count"], 1)


if __name__ == "__main__":
    unittest.main()
