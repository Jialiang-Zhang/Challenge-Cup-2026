import unittest

from agent.derivation_certificates import evaluate_decisive_derivation_certificates


class DecisiveDerivationCertificateTest(unittest.TestCase):
    def test_dangling_final_candidate_is_rejected(self):
        checks = evaluate_decisive_derivation_certificates(
            answer_raw="对 0<t<T，g_T 的分布函数为",
            response="F(t)=2/π arcsin sqrt(t/T).",
            requirements=("严格推导分布函数并给出密度",),
        )
        by_code = {item.code: item for item in checks}
        self.assertEqual(by_code["explicit_final_candidate_complete"].status, "fail")

    def test_explicit_formula_candidate_is_closed(self):
        checks = evaluate_decisive_derivation_certificates(
            answer_raw=r"F(t)=\frac2\pi\arcsin\sqrt{t/T}",
            response="完整推导。",
            requirements=("严格推导分布函数",),
        )
        by_code = {item.code: item for item in checks}
        self.assertEqual(by_code["explicit_final_candidate_complete"].status, "pass")

    def test_shearer_shortcut_without_ordered_chain_is_rejected(self):
        requirements = ("证明Shearer熵不等式，并明确使用条件越多条件熵越小",)
        bad = (
            r"由链式法则 dH(Z)=\sum_i H(Z_i\mid Z_{-i})+\sum_iH(Z_{-i})。"
            r"又 H(Z_i\mid Z_{-i})\le H(Z)，移项即得 (d-1)H(Z)\le\sum_iH(Z_{-i})。"
        )
        checks = evaluate_decisive_derivation_certificates(
            answer_raw="Shearer不等式成立",
            response=bad,
            requirements=requirements,
        )
        by_code = {item.code: item for item in checks}
        self.assertEqual(by_code["shearer_ordered_conditioning_chain"].status, "fail")

        good = (
            r"固定坐标顺序。对每个覆盖集S，用链式法则展开 H(Z_S)。"
            r"其中第j项条件于 S\cap\{1,\dots,j-1\}。"
            r"因为条件越多条件熵越小，该项不小于 H(Z_j\mid Z_1,\dots,Z_{j-1})。"
            r"对S求和，每个j出现d-1次，于是得到Shearer不等式。"
        )
        checks = evaluate_decisive_derivation_certificates(
            answer_raw="Shearer不等式成立",
            response=good,
            requirements=requirements,
        )
        by_code = {item.code: item for item in checks}
        self.assertEqual(by_code["shearer_ordered_conditioning_chain"].status, "pass")

    def test_bdf2_boundary_argument_needs_left_half_plane_anchor(self):
        requirements = (
            "利用根轨迹/边界轨迹证明整个左半平面包含在绝对稳定域内，并解释边界轨迹为什么不能割裂稳定分支",
        )
        bad = (
            r"对BDF2有 z(\theta)=(3-4e^{-i\theta}+e^{-2i\theta})/2，"
            r"边界完全在右半平面，所以左半平面属于稳定域。"
        )
        checks = evaluate_decisive_derivation_certificates(
            answer_raw="BDF2为A-稳定",
            response=bad,
            requirements=requirements,
        )
        by_code = {item.code: item for item in checks}
        self.assertEqual(by_code["stable_branch_interior_anchor"].status, "fail")

        good = (
            r"对BDF2边界轨迹有 Re z\ge0。取负实点 z=-1，特征方程为"
            r"5\zeta^2-4\zeta+1=0，两根模均小于1。"
            r"左半平面连通且内部没有单位圆根轨迹，因此稳定分支不能被割裂。"
        )
        checks = evaluate_decisive_derivation_certificates(
            answer_raw="BDF2为A-稳定",
            response=good,
            requirements=requirements,
        )
        by_code = {item.code: item for item in checks}
        self.assertEqual(by_code["stable_branch_interior_anchor"].status, "pass")

    def test_probability_cannot_equal_conditional_expectation_random_variable(self):
        bad = (
            r"\mathbb P(g_T\le t)=\mathbb E\Big[\mathbf 1_E\mid\mathcal F_t\Big]"
            r"=\mathbb E[\varphi(T-t,B_t)]."
        )
        checks = evaluate_decisive_derivation_certificates(
            answer_raw=r"F(t)=\frac2\pi\arcsin\sqrt{t/T}",
            response=bad,
            requirements=("利用Markov性质严格推导",),
        )
        by_code = {item.code: item for item in checks}
        self.assertEqual(by_code["conditional_expectation_type_consistency"].status, "fail")

        good = (
            r"由塔式性质，\mathbb P(E)=\mathbb E[\mathbb E[\mathbf 1_E\mid\mathcal F_t]]"
            r"=\mathbb E[\varphi(T-t,B_t)]."
        )
        checks = evaluate_decisive_derivation_certificates(
            answer_raw=r"F(t)=\frac2\pi\arcsin\sqrt{t/T}",
            response=good,
            requirements=("利用Markov性质严格推导",),
        )
        self.assertFalse(
            any(item.code == "conditional_expectation_type_consistency" and item.status == "fail" for item in checks)
        )


if __name__ == "__main__":
    unittest.main()
