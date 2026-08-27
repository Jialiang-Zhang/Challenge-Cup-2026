import unittest
from pathlib import Path

from llm_client import DEFAULT_MODEL


class ModelConfigurationTest(unittest.TestCase):
    def test_local_client_defaults_to_explicit_397b_model(self):
        self.assertEqual(DEFAULT_MODEL, "intern-s2-preview-397b")

    def test_benchmark_workflows_declare_explicit_397b_model(self):
        root = Path(__file__).resolve().parents[1]
        paths = (
            root / ".github/workflows/run-dev.yml",
            root / ".github/workflows/run-hard3-benchmark.yml",
            root / ".github/workflows/run-112-benchmark.yml",
        )
        expected = "INTERN_MODEL: intern-s2-preview-397b"
        ambiguous = "INTERN_MODEL: intern-s2-preview\n"
        for path in paths:
            text = path.read_text(encoding="utf-8")
            self.assertIn(expected, text, path.as_posix())
            self.assertNotIn(ambiguous, text, path.as_posix())


if __name__ == "__main__":
    unittest.main()
