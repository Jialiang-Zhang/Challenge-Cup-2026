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
            (dataset_dir / "1.json").write_text(
                json.dumps({"idx": 1, "problem": "p1", "answer": "a1"}),
                encoding="utf-8",
            )
            (dataset_dir / "0.json").write_text(
                json.dumps({"idx": 0, "problem": "p0", "answer": "a0"}),
                encoding="utf-8",
            )
            records = benchmark.load_dataset(dataset_dir, expected_count=2)
            self.assertEqual([item["idx"] for item in records], [0, 1])

    def test_load_dataset_rejects_noncontiguous_indices(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            dataset_dir = Path(temp_dir)
            (dataset_dir / "0.json").write_text(
                json.dumps({"idx": 0, "problem": "p0"}), encoding="utf-8"
            )
            (dataset_dir / "2.json").write_text(
                json.dumps({"idx": 2, "problem": "p2"}), encoding="utf-8"
            )
            with self.assertRaisesRegex(ValueError, "indices must be exactly"):
                benchmark.load_dataset(dataset_dir, expected_count=2)

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

    def test_build_summary_extracts_hora_telemetry(self) -> None:
        records = [
            {"idx": 0, "problem": "a", "answer": "-1/8", "subject": "algebra"},
            {"idx": 1, "problem": "b", "subject": "analysis"},
            {"idx": 2, "problem": "c", "subject": "analysis"},
        ]
        trace = [
            {
                "step": "profile",
                "content": {
                    "route": "R1",
                    "risk": "medium",
                    "domain": "abstract_algebra",
                },
            },
            {
                "step": "orthogonal_comparison",
                "content": {"orthogonality": "O3", "equivalence": "equivalent"},
            },
            {"step": "red_team_result", "content": {"verdict": "ACCEPT_A"}},
            {
                "step": "transaction_commit",
                "content": {
                    "source": "primary",
                    "model_calls": 3,
                    "repair_count": 0,
                },
            },
        ]
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)
            (output_dir / "0.json").write_text(
                json.dumps(
                    {
                        "idx": 0,
                        "status": "success",
                        "final_response": r"-\frac{1}{8}",
                        "trace": trace,
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
            self.assertEqual(
                summary["counts"],
                {"success": 1, "error": 1, "missing": 1, "other": 0},
            )
            self.assertEqual(summary["subjects"], {"algebra": 1, "analysis": 2})
            self.assertEqual(summary["telemetry"]["model_calls_total"], 3)
            self.assertEqual(summary["telemetry"]["routes"], {"R1": 1, "unknown": 2})
            self.assertEqual(
                summary["reference_evaluation"]["counts"]["equivalent"], 1
            )
            self.assertEqual(summary["records"][0]["orthogonality"], "O3")

    def test_incomplete_outputs_produce_nonzero_exit_code(self) -> None:
        incomplete = {
            "total": 3,
            "counts": {"success": 2, "error": 1, "missing": 0, "other": 0},
        }
        complete = {
            "total": 3,
            "counts": {"success": 3, "error": 0, "missing": 0, "other": 0},
        }
        self.assertEqual(benchmark.derive_benchmark_exit_code(incomplete, 0), 2)
        self.assertEqual(benchmark.derive_benchmark_exit_code(complete, 0), 0)
        self.assertEqual(benchmark.derive_benchmark_exit_code(complete, 7), 7)


if __name__ == "__main__":
    unittest.main()
