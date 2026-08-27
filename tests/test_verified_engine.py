import unittest

from agent.models import AgentConfig, CaseState, MethodFingerprint, SolutionCapsule, TaskContract
from agent.runtime import RuntimeGuard
from agent.verified_engine import VerifiedHORAEngine, proof_revision_markers


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


def proof_contract():
    return TaskContract(
        primary_domain="discrete_combinatorics",
        secondary_domains=(),
        problem_kind="proof",
        answer_schema="proof",
        requires_proof=True,
        requires_exact_answer=False,
        multipart_count=1,
        risk_level="high",
        verification_modes=("theorem_precondition",),
        mandatory_attacks=("transformation", "completeness"),
        likely_failure_modes=("sign_error", "inequality_direction"),
        route_hint="R2",
        primary_method="theorem",
        orthogonal_method="constructive",
        question_mode="proof",
        answer_obligations=("proof_chain",),
    )


def capsule(candidate_id="A", response=None):
    return SolutionCapsule(
        candidate_id=candidate_id,
        source="primary" if candidate_id == "A" else "orthogonal_blind",
        answer_raw="结论成立",
        final_response=response
        or "由链式法则得到第一步。因为条件越多条件熵越小，所以各项方向一致。最终求和得到目标不等式，证毕。",
        fingerprint=MethodFingerprint(paradigm="theorem"),
        complete=True,
        truncated=False,
        protocol_complete=True,
    )


class VerifiedEngineTest(unittest.TestCase):
    def test_multiple_proof_restarts_are_flagged(self):
        text = (
            "先得到一个不等式。实际上这里需要重新判断方向。"
            "更准确地，应使用条件熵单调性。标准论证如下：重新按链式法则求和，证毕。"
        )
        markers = proof_revision_markers(text)
        self.assertGreaterEqual(len(markers), 2)

        engine = VerifiedHORAEngine(client=FakeClient([]), config=AgentConfig())
        state = CaseState(contract=proof_contract())
        item = capsule(response=text)
        state.add_candidate(item)
        engine._apply_candidate_evidence(state, item)
        revision = [
            evidence
            for evidence in state.evidence
            if evidence.evidence_type == "proof_internal_revision_conflict"
        ]
        self.assertEqual(len(revision), 1)
        self.assertEqual(revision[0].status, "fail")
        self.assertFalse(state.candidates["A"].eligible)

    def test_single_clarification_does_not_trigger_revision_gate(self):
        text = "由链式法则得到等式。更准确地说，条件集合包含全部先前坐标，因此不等式方向如上。证毕。"
        self.assertLess(len(proof_revision_markers(text)), 2)

    def test_confirmation_accept_requires_concrete_witness(self):
        response = """
<VERDICT>ACCEPT_A</VERDICT>
<TARGET_CANDIDATE>A</TARGET_CANDIDATE>
<TARGET_CLAIM>C1</TARGET_CLAIM>
<ATTACK_TYPE>none</ATTACK_TYPE>
<SEVERITY>none</SEVERITY>
<CHALLENGE>none</CHALLENGE>
<WITNESS>none</WITNESS>
<RESOLVER_HINT>none</RESOLVER_HINT>
"""
        client = FakeClient([response])
        config = AgentConfig(max_model_calls=2)
        engine = VerifiedHORAEngine(client=client, config=config)
        state = CaseState(contract=proof_contract())
        item = capsule()
        state.add_candidate(item)
        guard = RuntimeGuard(config)
        result = engine._confirmation_result(
            problem="证明目标不等式。",
            state=state,
            guard=guard,
            trace=[],
            selected=item,
        )
        self.assertEqual(result.verdict, "UNRESOLVED")
        self.assertFalse(
            any(e.evidence_type == "decisive_confirmation" for e in state.evidence)
        )

    def test_confirmation_repair_maps_to_actual_candidate(self):
        response = """
<VERDICT>REPAIR_A</VERDICT>
<TARGET_CANDIDATE>A</TARGET_CANDIDATE>
<TARGET_CLAIM>C2</TARGET_CLAIM>
<ATTACK_TYPE>transformation</ATTACK_TYPE>
<SEVERITY>major</SEVERITY>
<CHALLENGE>The displayed coefficient is off by a factor of two.</CHALLENGE>
<WITNESS>Direct Taylor expansion gives -2 h^3/3, not -h^3/3.</WITNESS>
<RESOLVER_HINT>Recompute the cubic Taylor coefficient.</RESOLVER_HINT>
"""
        client = FakeClient([response])
        config = AgentConfig(max_model_calls=2)
        engine = VerifiedHORAEngine(client=client, config=config)
        state = CaseState(contract=proof_contract())
        item = capsule(candidate_id="B")
        state.add_candidate(item)
        guard = RuntimeGuard(config)
        result = engine._confirmation_result(
            problem="严格证明数值格式的阶数。",
            state=state,
            guard=guard,
            trace=[],
            selected=item,
        )
        self.assertEqual(result.verdict, "REPAIR_A")
        self.assertEqual(result.target_candidate_id, "B")
        self.assertFalse(state.candidates["B"].eligible)
        self.assertTrue(
            any(ch.candidate_id == "B" and ch.status == "sustained" for ch in state.challenges)
        )


if __name__ == "__main__":
    unittest.main()
