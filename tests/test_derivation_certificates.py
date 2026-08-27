import unittest

from agent.requirement_checks import evaluate_explicit_requirement_coverage


class DerivationCertificateTest(unittest.TestCase):
    def test_rejects_abandoned_proof_drafts(self):
        requirements = ("先证明Shearer熵不等式，并明确使用条件越多条件熵越小。",)
        response = (
            "先尝试一个展开。更直接地可写另一式。"
            "但最简洁的标准论证如下。更准确地，需要换一个条件集合。"
            "标准结论是最后一个不等式成立。"
        )
        checks = evaluate_explicit_requirement_coverage(response, requirements)
        by_code = {item.code: item for item in checks}
        self.assertEqual(by_code["clean_proof_chain"].status, "fail")
        self.assertTrue(by_code["clean_proof_chain"].hard_failure)

    def test_rejects_wrong_bdf2_third_derivative_coefficient(self):
        requirements = (
            "由局部截断误差验证二阶精度",
            r"利用根轨迹/边界轨迹 z(\theta)=(3-4e^{-i\theta}+e^{-2i\theta})/2 证明A-稳定",
        )
        wrong = (
            r"3y_{n+2}-4y_{n+1}+y_n=2hy'-\frac{h^3}{3}y'''+O(h^4)，"
            r"所以除以2h后为 y'-\frac{h^2}{6}y'''+O(h^3)。"
        )
        checks = evaluate_explicit_requirement_coverage(wrong, requirements)
        by_code = {item.code: item for item in checks}
        self.assertEqual(by_code["bdf2_taylor_coefficient"].status, "fail")

        correct = (
            r"3y_{n+2}-4y_{n+1}+y_n=2hy'-\frac{2}{3}h^3y'''+O(h^4)，"
            r"所以除以2h后为 y'-\frac{1}{3}h^2y'''+O(h^3)。"
        )
        checks = evaluate_explicit_requirement_coverage(correct, requirements)
        by_code = {item.code: item for item in checks}
        self.assertEqual(by_code["bdf2_taylor_coefficient"].status, "pass")

    def test_rejects_doubled_brownian_gaussian_prefactor(self):
        requirements = (
            r"定义最后一次过零时刻 g_T，利用Markov性质、反射原理与高斯积分严格推导分布函数并给出密度。",
        )
        wrong = (
            r"条件于B_t=x后，由反射原理积分。作x=\sqrt t u后，"
            r"F(t)=\frac{4}{\pi}\int_{0}^{\infty}e^{-u^2/2}"
            r"\int_{0}^{au}e^{-y^2/2}\,dy\,du，"
            r"最后写成\frac{2}{\pi}\arctan a。"
        )
        checks = evaluate_explicit_requirement_coverage(wrong, requirements)
        by_code = {item.code: item for item in checks}
        self.assertEqual(by_code["brownian_last_zero_gaussian_normalization"].status, "fail")

        correct = (
            r"条件于B_t=x后，由反射原理积分。作x=\sqrt t u后，"
            r"F(t)=\frac{2}{\pi}\int_{0}^{\infty}e^{-u^2/2}"
            r"\int_{0}^{au}e^{-y^2/2}\,dy\,du"
            r"=\frac{2}{\pi}\arctan a。"
        )
        checks = evaluate_explicit_requirement_coverage(correct, requirements)
        by_code = {item.code: item for item in checks}
        self.assertEqual(by_code["brownian_last_zero_gaussian_normalization"].status, "pass")


if __name__ == "__main__":
    unittest.main()
