import unittest

from agent.derivation_certificates import evaluate_decisive_derivation_certificates
from agent.verified_engine import proof_revision_markers


class ProofConsistencyCertificateTest(unittest.TestCase):
    def test_shearer_wrong_conditioning_direction_is_rejected(self):
        requirements = (
            "先证明Shearer熵不等式，并明确使用条件越多条件熵越小。",
        )
        wrong = r"""
        由链式法则 H(Z)=\sum_j H(Z_j\mid Z_1,\dots,Z_{j-1})。
        对 H(Z_{-i})，我们把 Z_j 条件在除 i,j 外的更多变量上。
        这里条件集合比 H(Z_j\mid Z_1,\dots,Z_{j-1}) 的条件集合多了变量，
        因而 H(Z_j\mid \text{更多变量})\le H(Z_j\mid Z_1,\dots,Z_{j-1})。
        于是 \sum_{i=1}^d H(Z_{-i})\ge(d-1)H(Z)。
        """
        checks = evaluate_decisive_derivation_certificates(
            answer_raw="Shearer成立",
            response=wrong,
            requirements=requirements,
        )
        by_code = {item.code: item for item in checks}
        self.assertEqual(by_code["shearer_ordered_conditioning_chain"].status, "fail")
        self.assertTrue(by_code["shearer_ordered_conditioning_chain"].hard_failure)

    def test_shearer_less_conditioning_chain_is_accepted(self):
        requirements = (
            "先证明Shearer熵不等式，并明确使用条件越多条件熵越小。",
        )
        correct = r"""
        固定坐标顺序。由链式法则
        H(Z)=\sum_j H(Z_j\mid Z_1,\dots,Z_{j-1})。
        在 H(Z_{-i}) 的链式展开中，第 j 项只条件于
        Z_1,\dots,Z_{j-1} 中除去 Z_i 后仍存在的变量，因此条件更少。
        条件更少时条件熵更大，所以
        H(Z_j\mid Z_{<j}\setminus\{Z_i\})\ge H(Z_j\mid Z_1,\dots,Z_{j-1})。
        对 i 求和，每个 j 恰出现 d-1 次，故
        \sum_i H(Z_{-i})\ge(d-1)H(Z)。
        """
        checks = evaluate_decisive_derivation_certificates(
            answer_raw="Shearer成立",
            response=correct,
            requirements=requirements,
        )
        by_code = {item.code: item for item in checks}
        self.assertEqual(by_code["shearer_ordered_conditioning_chain"].status, "pass")

    def test_bdf2_taylor_half_cannot_disappear_during_substitution(self):
        requirements = ("由局部截断误差验证BDF2二阶精度",)
        wrong = r"""
        y(t_{n+1})=y(t_{n+2})-hy'(t_{n+2})+\frac{h^2}{2}y''(t_{n+2})+O(h^3)。
        代入 3y_{n+2}-4y_{n+1}+y_n 时写成
        -4\Bigl(y-hy'+\frac{h^2}y''-\frac{h^3}{6}y'''\Bigr)，
        最后声称局部截断误差为 O(h^2)。
        """
        checks = evaluate_decisive_derivation_certificates(
            answer_raw="二阶",
            response=wrong,
            requirements=requirements,
        )
        by_code = {item.code: item for item in checks}
        self.assertEqual(by_code["bdf2_taylor_substitution_consistency"].status, "fail")
        self.assertTrue(by_code["bdf2_taylor_substitution_consistency"].hard_failure)

    def test_explicit_retraction_marker_is_detected(self):
        proof = (
            "先得到某矩阵的谱。实际上还需补一步。"
            "其余特征值的乘积为某式？不，应重新整理。"
            "正确结论如下。"
        )
        markers = proof_revision_markers(proof)
        self.assertIn("explicit_retraction", markers)

    def test_polished_alternative_phrase_alone_is_not_retraction(self):
        proof = "更直接地，我们也可以由矩阵树定理完成最后一步，因此结论成立。"
        markers = proof_revision_markers(proof)
        self.assertNotIn("explicit_retraction", markers)
        self.assertLess(len(markers), 3)


if __name__ == "__main__":
    unittest.main()
