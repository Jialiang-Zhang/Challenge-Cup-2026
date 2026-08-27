import unittest

from agent.canonicalize import compare_answers, normalize_answer_text, numeric_value


class CanonicalizeTest(unittest.TestCase):
    def test_latex_fraction_equivalence(self) -> None:
        self.assertEqual(compare_answers("-1/8", r"-\frac{1}{8}"), "equivalent")
        self.assertEqual(compare_answers("1/2", "0.5"), "equivalent")

    def test_symbolic_equivalence(self) -> None:
        self.assertEqual(compare_answers("sin(x)^2+cos(x)^2", "1"), "equivalent")

    def test_distinct_exact_numbers(self) -> None:
        self.assertEqual(compare_answers("1/8", "-1/8"), "not_equivalent")

    def test_boxed_and_prefix_normalization(self) -> None:
        self.assertEqual(normalize_answer_text(r"最终答案：$\boxed{72}$。"), "72")

    def test_numeric_value(self) -> None:
        self.assertAlmostEqual(numeric_value(r"-\frac{1}{8}"), -0.125)


if __name__ == "__main__":
    unittest.main()
