import unittest

from agent.adaptive_engine import AdaptiveVerifiedHORAEngine
from agent.cross_domain_certificates import evaluate_cross_domain_certificates
from agent.models import AgentConfig, CaseState, TaskContract
from agent.runtime import RuntimeGuard


class FakeClient:
    def __init__(self):
        self.calls = []

    def chat(self, **kwargs):
        self.calls.append(kwargs)
        return "ok"


def contract() -> TaskContract:
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
        mandatory_attacks=("theorem_precondition",),
        likely_failure_modes=("coefficient_error",),
        route_hint="R2",
        primary_method="theorem",
        orthogonal_method="constructive",
        question_mode="proof",
        answer_obligations=("proof_chain",),
    )


class RecoveryRound12Test(unittest.TestCase):
    def test_complete_radau_proof_gets_positive_certificate(self):
        response = r"""
        两级 Radau IIA 的稳定函数为
        R(z)=\frac{1+z/3}{1-2z/3+z^2/6}.
        对 z=i\omega，
        |R(i\omega)|^2=\frac{1+\omega^2/9}{1+\omega^2/9+\omega^4/36}\le1.
        分母的两个零点为 2\pm i\sqrt2，均在右半平面，因此 R 在闭左半平面解析。
        由最大模原理，整个左半平面满足 |R(z)|\le1。
        且 \lim_{z\to\infty}R(z)=0，故方法也为 L-稳定。
        """
        checks = evaluate_cross_domain_certificates(answer_raw="A稳定且L稳定", response=response)
        by_code = {item.code: item for item in checks}
        self.assertEqual(by_code["radau_internal_arithmetic"].status, "pass")
        self.assertEqual(by_code["radau_full_stability_certificate"].status, "pass")
        self.assertFalse(by_code["radau_full_stability_certificate"].hard_failure)

    def test_incomplete_radau_proof_does_not_get_positive_certificate(self):
        response = r"""
        Radau IIA 的稳定函数为 R(z)=\frac{1+z/3}{1-2z/3+z^2/6}。
        在虚轴上 |R(i\omega)|\le1，因此它是 A-稳定的。
        """
        checks = evaluate_cross_domain_certificates(answer_raw="A稳定", response=response)
        by_code = {item.code: item for item in checks}
        self.assertNotEqual(by_code["radau_full_stability_certificate"].status, "pass")

    def test_targeted_repair_gets_at_least_3072_tokens(self):
        client = FakeClient()
        config = AgentConfig(primary_max_tokens=4096, repair_max_tokens=1024, max_model_calls=6)
        engine = AdaptiveVerifiedHORAEngine(client=client, config=config)
        state = CaseState(contract=contract())
        guard = RuntimeGuard(config)
        trace = []

        result = engine._call_model(
            state=state,
            guard=guard,
            trace=trace,
            step="targeted_repair_call",
            prompt="repair this proof",
            temperature=0.0,
            max_tokens=1024,
            thinking_mode=False,
        )
        self.assertEqual(result, "ok")
        self.assertEqual(client.calls[-1]["max_tokens"], 3072)
        prompt = client.calls[-1]["messages"][0]["content"]
        self.assertIn("COMPACT REPAIR PRIORITY", prompt)
        self.assertIn("Close FINAL_CANDIDATE and FINAL_RESPONSE", prompt)


if __name__ == "__main__":
    unittest.main()
