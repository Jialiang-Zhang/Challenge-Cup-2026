import unittest

from agent.adaptive_engine import _task_driven_guardrails
from agent.cross_domain_certificates import evaluate_cross_domain_certificates


class CrossDomainRound10Test(unittest.TestCase):
    def _codes(self, response: str, answer: str = "ok"):
        checks = evaluate_cross_domain_certificates(answer_raw=answer, response=response)
        return {item.code: item for item in checks}

    def test_radau_latex_fraction_conflicts_are_rejected(self):
        bad = r"""
        Radau IIA. R(z)=\frac{1+\frac13 z}{1-\frac23 z+\frac16 z^2}.
        Second component: \frac{1+\frac16 z}{\Delta}.
        |R(iw)|^2=\frac{1+\frac19w^2}{1+\frac{10}{9}w^2+\frac1{36}w^4}.
        """
        by_code = self._codes(bad)
        self.assertEqual(by_code["radau_internal_arithmetic"].status, "fail")

        good = r"""
        Radau IIA. R(z)=\frac{1+\frac13 z}{1-\frac23 z+\frac16 z^2}.
        Second component: \frac{1+\frac13 z}{\Delta}.
        |R(iw)|^2=\frac{1+\frac19w^2}{1+\frac19w^2+\frac1{36}w^4}.
        """
        by_code = self._codes(good)
        self.assertEqual(by_code["radau_internal_arithmetic"].status, "pass")

    def test_levy_l1_bounded_doob_upgrade_is_rejected_from_candidate_itself(self):
        bad = (
            r"M_n=\mathbb E[X\mid\mathcal F_n]是L^1有界鞅。"
            "由Doob鞅收敛定理，存在极限使M_n几乎处处且在L^1中收敛。"
        )
        by_code = self._codes(bad)
        self.assertEqual(by_code["levy_upward_requires_ui"].status, "fail")

        good = (
            r"M_n=\mathbb E[X\mid\mathcal F_n]。"
            "先证明这一族一致可积，再由鞅收敛定理得到a.s.与L^1收敛。"
        )
        by_code = self._codes(good)
        self.assertEqual(by_code["levy_upward_requires_ui"].status, "pass")

    def test_holonomy_closed_loop_original_direction_claim_is_rejected(self):
        bad = (
            r"由d\theta=-\omega和d\omega=-K\,dA可计算曲率积分。"
            "闭合回路整体定向要求向量最终回到原方向，因此再加入三个外角。"
        )
        by_code = self._codes(bad)
        self.assertEqual(by_code["holonomy_no_false_closed_return"].status, "fail")

        good = (
            r"由d\theta=-\omega和d\omega=-K\,dA，Stokes直接给holonomy角。"
            "再独立对测地三角形使用Gauss-Bonnet处理外角。"
        )
        by_code = self._codes(good)
        self.assertEqual(by_code["holonomy_no_false_closed_return"].status, "pass")

    def test_bare_chinese_has_is_not_a_complete_proof_conclusion(self):
        by_code = self._codes("正文完整。", answer="设M满足条件，则对任意u与s<t，有")
        self.assertEqual(by_code["proof_conclusion_self_contained"].status, "fail")

    def test_multiselect_guard_requires_all_options_evaluated(self):
        problem = (
            "判断下列结论哪些正确：A. 二阶；B. A稳定；C. 保持二次不变量；D. 对所有能量精确保留。"
        )
        guard = _task_driven_guardrails(problem)
        self.assertIn("MULTI-SELECT COMPLETENESS GUARD", guard)
        self.assertIn("EVERY labelled option", guard)


if __name__ == "__main__":
    unittest.main()
