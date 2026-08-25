import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "run_112_benchmark.py"
SPEC = importlib.util.spec_from_file_location("run_112_benchmark", MODULE_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("Unable to load benchmark module")
benchmark = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(benchmark)


class Run112BenchmarkTest(unittest.TestCase):
    def test_load_dataset_sorts_by_idx_and_validates_count(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            dataset_dir = Path(temp_dir)
            (dataset_dir / "10.json").write_text(
                json.dumps({"idx": 10, "problem": "p10", "answer": "a10"}),
                encoding="utf-8",
            )
            (dataset_dir / "2.json").write_text(
                json.dumps({"idx": 2, "problem": "p2", "answer": "a2"}),
                encoding="utf-8",
            )

            records = benchmark.load_dataset(dataset_dir, expected_count=2)
            self.assertEqual([item["idx"] for item in records], [2, 10])

    def test_write_agent_input_excludes_reference_fields(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            input_file = Path(temp_dir) / "input.jsonl"
            benchmark.write_agent_input(
                [
                    {
                        "idx": 0,
                        "problem": "problem",
                        "answer": "secret-reference",
                        "subject": "algebra",
                        "source": "test",
                    }
                ],
                input_file,
            )

            item = json.loads(input_file.read_text(encoding="utf-8"))
            self.assertEqual(item, {"idx": 0, "problem": "problem"})

    def test_build_summary_counts_success_error_and_missing(self) -> None:
        records = [
            {"idx": 0, "problem": "a", "subject": "algebra"},
            {"idx": 1, "problem": "b", "subject": "analysis"},
            {"idx": 2, "problem": "c", "subject": "analysis"},
        ]

        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)
            (output_dir / "0.json").write_text(
                json.dumps(
                    {
                        "idx": 0,
                        "status": "success",
                        "final_response": "42",
                        "trace": [{"step": "finalize"}],
                    }
                ),
                encoding="utf-8",
            )
            (output_dir / "1.json").write_text(
                json.dumps(
                    {
                        "idx": 1,
                        "status": "error",
                        "final_response": "",
                        "error": {"type": "RuntimeError"},
                        "trace": [],
                    }
                ),
                encoding="utf-8",
            )

            summary = benchmark.build_summary(
                records,
                output_dir,
                run_id="20260825T120000Z-test",
                runner_exit_code=0,
            )

            self.assertEqual(summary["counts"]["success"], 1)
            self.assertEqual(summary["counts"]["error"], 1)
            self.assertEqual(summary["counts"]["missing"], 1)
            self.assertEqual(summary["subjects"], {"algebra": 1, "analysis": 2})
            self.assertEqual(summary["records"][0]["response_chars"], 2)
            self.assertEqual(summary["records"][0]["trace_steps"], 1)


if __name__ == "__main__":
    unittest.main()
