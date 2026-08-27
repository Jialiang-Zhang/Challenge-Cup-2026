import unittest

from agent.adaptive_engine import _task_driven_guardrails


class AdaptiveGuardrailsRound9Test(unittest.TestCase):
    def test_original_filtration_guard(self):
        text = _task_driven_guardrails(
            "设M为连续局部鞅。证明M是相对于其原滤过的Brownian运动，要求从指数鞅出发。"
        )
        self.assertIn("ORIGINAL-FILTRATION GUARD", text)
        self.assertIn("ORIGINAL filtration", text)

    def test_levy_upward_guard(self):
        text = _task_driven_guardrails(
            r"设\mathcal F_n\uparrow\mathcal F_\infty，证明\mathbb E[X\mid\mathcal F_n]在L1中收敛。"
        )
        self.assertIn("LEVY-UPWARD GUARD", text)
        self.assertIn("does NOT imply L1 convergence", text)

    def test_holonomy_guard(self):
        text = _task_driven_guardrails(
            "利用联络1-形式与Gauss-Bonnet证明沿边界平行移动的holonomy角。"
        )
        self.assertIn("HOLONOMY SIGN GUARD", text)
        self.assertIn("does NOT return", text)

    def test_james_stein_guard(self):
        text = _task_driven_guardrails(
            r"对James--Stein估计量\delta_a利用Stein恒等式推导风险并确定a的范围。"
        )
        self.assertIn("JAMES-STEIN RANGE GUARD", text)
        self.assertIn("endpoints included", text)

    def test_multi_object_algebra_guard(self):
        text = _task_driven_guardrails(
            r"完整描述\operatorname{Spec}R和极大理想，求极小素理想、nilradical与全部零因子并说明约化。"
        )
        self.assertIn("MULTI-OBJECT ALGEBRA GUARD", text)
        self.assertIn("complete zero-divisor set", text)


if __name__ == "__main__":
    unittest.main()
