import unittest

from agent.derivation_certificates import evaluate_decisive_derivation_certificates


class DecisiveCertificateRegressionTest(unittest.TestCase):
    def test_rejects_false_shearer_marginal_shortcut(self):
        requirements = ("先证明Shearer熵不等式，并明确使用条件越多条件熵越小。",)
        response = (
            r"固定坐标顺序，用链式法则展开。"
            r"由H(Z_i\mid Z_{-i})\ge0，因此得到 H(Z)\le H(Z_{-i})。"
            r"随后再按覆盖次数求和。"
        )
        checks = evaluate_decisive_derivation_certificates(
            answer_raw="Loomis--Whitney成立",
            response=response,
            requirements=requirements,
        )
        by_code = {item.code: item for item in checks}
        self.assertEqual(by_code["shearer_ordered_conditioning_chain"].status, "fail")
        self.assertTrue(by_code["shearer_ordered_conditioning_chain"].hard_failure)

    def test_accepts_clean_shearer_ordered_prefix_chain(self):
        requirements = ("先证明Shearer熵不等式，并明确使用条件越多条件熵越小。",)
        response = (
            r"固定坐标顺序。对每个Z_{-i}按自然顺序链式展开。"
            r"对j\ne i，其条件集合是Z_1,\dots,Z_{j-1}的子集，条件更少，故"
            r"H(Z_j\mid Z_1,\dots,Z_{j-1}\text{去掉}Z_i)\ge"
            r"H(Z_j\mid Z_1,\dots,Z_{j-1})。"
            r"对i,j求和，每个j出现d-1次，得到Shearer不等式。"
        )
        checks = evaluate_decisive_derivation_certificates(
            answer_raw="Loomis--Whitney成立",
            response=response,
            requirements=requirements,
        )
        by_code = {item.code: item for item in checks}
        self.assertEqual(by_code["shearer_ordered_conditioning_chain"].status, "pass")

    def test_accepts_negative_real_asymptotic_as_bdf2_anchor(self):
        requirements = (
            r"利用根轨迹/边界轨迹证明整个左半平面包含在绝对稳定域内，并解释为什么边界轨迹不可能把左半平面的稳定分支割裂。",
        )
        response = (
            r"对BDF2，边界轨迹完全位于右半平面。沿负实轴令z\to-\infty，"
            r"特征方程的两个根都趋于0，因此最终都在单位圆内部。"
            r"左半平面连通且其中没有单位圆根轨迹，所以整个左半平面属于同一稳定分支。"
        )
        checks = evaluate_decisive_derivation_certificates(
            answer_raw="BDF2为A-稳定",
            response=response,
            requirements=requirements,
        )
        by_code = {item.code: item for item in checks}
        self.assertEqual(by_code["stable_branch_interior_anchor"].status, "pass")


if __name__ == "__main__":
    unittest.main()
