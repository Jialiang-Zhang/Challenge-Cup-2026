import unittest

from agent.models import MethodFingerprint
from agent.orthogonality import orthogonality_level
from agent.routing import build_task_contract


class RoutingTest(unittest.TestCase):
    def test_high_risk_measure_proof(self) -> None:
        contract = build_task_contract(
            "证明在支配收敛定理条件下可以交换极限与Lebesgue积分，并严格说明可测性。"
        )
        self.assertEqual(contract.primary_domain, "measure_theory")
        self.assertEqual(contract.risk_level, "high")
        self.assertTrue(contract.requires_proof)
        self.assertIn("theorem_precondition", contract.mandatory_attacks)

    def test_low_risk_complex_calculation(self) -> None:
        contract = build_task_contract("求函数 f(z)=1/(z-1) 在 z=1 处的留数。")
        self.assertEqual(contract.primary_domain, "complex_analysis")
        self.assertEqual(contract.risk_level, "low")

    def test_orthogonality_gate(self) -> None:
        structural = MethodFingerprint(
            paradigm="theorem",
            representation="symbolic",
            theorem_family="structure theorem",
            tool_channel="none",
        )
        constructive = MethodFingerprint(
            paradigm="constructive",
            representation="coordinate",
            theorem_family="definition",
            tool_channel="brute_force",
        )
        self.assertEqual(orthogonality_level(structural, constructive), "O3")

        copied = MethodFingerprint(
            paradigm="theorem",
            representation="symbolic",
            theorem_family="structure theorem",
            tool_channel="none",
            exposed_to_primary=True,
        )
        self.assertEqual(orthogonality_level(structural, copied), "O0")


if __name__ == "__main__":
    unittest.main()
