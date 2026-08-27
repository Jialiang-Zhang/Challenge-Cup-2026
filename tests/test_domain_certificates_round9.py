import unittest

from agent.derivation_certificates import evaluate_decisive_derivation_certificates
from agent.task_profile import analyze_task, normalized_choice_letters


class CrossDomainCertificateTest(unittest.TestCase):
    def _codes(self, *, answer="ok", response, requirements=()):
        checks = evaluate_decisive_derivation_certificates(
            answer_raw=answer,
            response=response,
            requirements=tuple(requirements),
        )
        return {item.code: item for item in checks}

    def test_inline_which_are_correct_is_multiselect(self):
        problem = (
            "判断下列结论哪些正确：A. 命题甲；B. 命题乙；C. 命题丙；D. 命题丁。"
        )
        profile = analyze_task(problem)
        self.assertEqual(profile.mode, "choice")
        self.assertIn("choice_letters", profile.obligations)
        self.assertNotIn("binary_verdict", profile.obligations)

    def test_truth_annotated_choice_answer_normalizes_selected_letters(self):
        self.assertEqual(normalized_choice_letters("A正确;B正确;C正确;D错误"), ("A", "B", "C"))
        self.assertEqual(normalized_choice_letters("A、B、C正确，D错误"), ("A", "B", "C"))

    def test_rejects_l1_bounded_martingale_shortcut(self):
        requirements = (
            r"证明 M_n=\mathbb E[X\mid\mathcal F_n] 几乎处处且在 L^1 中收敛。",
        )
        bad = (
            "先设X非负，则M_n是非负L^1有界鞅。由Doob鞅收敛定理，"
            "存在M使M_n几乎处处收敛且在L^1中收敛。"
        )
        by_code = self._codes(response=bad, requirements=requirements)
        self.assertEqual(by_code["levy_upward_uniform_integrability"].status, "fail")

        good = (
            "条件期望族{E[X|F_n]}一致可积，因此鞅收敛定理给出a.s.与L^1收敛。"
            "再用单调类定理识别极限为E[X|F_infty]。"
        )
        by_code = self._codes(response=good, requirements=requirements)
        self.assertEqual(by_code["levy_upward_uniform_integrability"].status, "pass")

    def test_rejects_holonomy_sign_discard(self):
        requirements = (
            "利用活动标架、联络1-形式与Gauss-Bonnet证明平行移动holonomy角。",
        )
        bad = (
            r"由d\theta=-\omega得\Delta\theta=-\oint\omega。"
            "但向量回到起点时方向不变，所以改取Theta=oint omega。"
            r"又有\Theta=-\int KdA\equiv\int KdA\pmod{2\pi}，负号由方向约定吸收。"
        )
        by_code = self._codes(response=bad, requirements=requirements)
        self.assertEqual(by_code["holonomy_orientation_consistency"].status, "fail")

        good = (
            r"平行条件给d\theta=-\omega，故\Delta\theta=-\oint_{\partial\Delta}\omega。"
            r"由d\omega=-K\,dA和Stokes，\Delta\theta=-\int d\omega=\int K\,dA。"
        )
        by_code = self._codes(response=good, requirements=requirements)
        self.assertEqual(by_code["holonomy_orientation_consistency"].status, "pass")

    def test_original_filtration_cannot_be_replaced_by_natural_filtration(self):
        requirements = (
            "证明M是相对于其原滤过的标准Brownian运动。",
            "要求从指数鞅出发证明增量的条件特征函数。",
        )
        bad = (
            r"设\mathcal F_t^M=\sigma(M_s:s\le t)为自然滤过。"
            r"计算E[e^{iu(M_t-M_s)}|\mathcal F_s^M]，故M关于自然滤过为Brownian运动。"
        )
        by_code = self._codes(response=bad, requirements=requirements)
        self.assertEqual(by_code["original_filtration_obligation"].status, "fail")

        good = (
            r"对原滤过(\mathcal F_t)，指数鞅满足E[Z_t|\mathcal F_s]=Z_s，"
            r"从而E[e^{iu(M_t-M_s)}|\mathcal F_s]=e^{-u^2(t-s)/2}。"
        )
        by_code = self._codes(response=good, requirements=requirements)
        self.assertEqual(by_code["original_filtration_obligation"].status, "pass")

    def test_rejects_open_interval_as_full_james_stein_nonincrease_range(self):
        bad = (
            r"对James--Stein估计量\delta_a，Stein恒等式给风险差"
            r"[a^2-2a(p-2)]E(1/\|X\|^2)。"
            r"故当且仅当0<a<2(p-2)时，对所有theta风险不增。"
        )
        by_code = self._codes(response=bad)
        self.assertEqual(by_code["james_stein_endpoint_range"].status, "fail")

        good = (
            r"对James--Stein估计量\delta_a，Stein恒等式给风险差"
            r"[a^2-2a(p-2)]E(1/\|X\|^2)。"
            r"因此0\le a\le2(p-2)时风险不增；0<a<2(p-2)时严格降低。"
        )
        by_code = self._codes(response=good)
        self.assertEqual(by_code["james_stein_endpoint_range"].status, "pass")

    def test_rejects_radau_imaginary_axis_coefficient_error(self):
        requirements = ("考虑两级Radau IIA方法并严格证明A稳定。",)
        bad = (
            r"R(z)=\frac{1+z/3}{1-2z/3+z^2/6}。"
            r"在虚轴上|R(i\omega)|^2=\frac{1+\omega^2/9}"
            r"{1+\omega^2/3+\omega^4/36}。"
        )
        by_code = self._codes(response=bad, requirements=requirements)
        self.assertEqual(by_code["runge_kutta_stability_arithmetic"].status, "fail")

        good = (
            r"R(z)=\frac{1+z/3}{1-2z/3+z^2/6}。"
            r"在虚轴上|R(i\omega)|^2=\frac{1+\omega^2/9}"
            r"{1+\omega^2/9+\omega^4/36}\le1。"
        )
        by_code = self._codes(response=good, requirements=requirements)
        self.assertEqual(by_code["runge_kutta_stability_arithmetic"].status, "pass")


if __name__ == "__main__":
    unittest.main()
