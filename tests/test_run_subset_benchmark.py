import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "run_subset_benchmark.py"
SPEC = importlib.util.spec_from_file_location("run_subset_benchmark", MODULE_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("Unable to load subset benchmark module")
subset = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(subset)


class RunSubsetBenchmarkTest(unittest.TestCase):
    def test_parse_indices_rejects_duplicates_and_non_numeric_values(self) -> None:
        self.assertEqual(subset.parse_indices("0,40,70"), (0, 40, 70))
        with self.assertRaises(ValueError):
            subset.parse_indices("0,40,40")
        with self.assertRaises(ValueError):
            subset.parse_indices("0,x")

    def test_selected_dataset_and_agent_input_are_isolated(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            dataset_dir = Path(temp_dir) / "dataset"
            dataset_dir.mkdir()
            for idx in (0, 40, 70):
                (dataset_dir / f"{idx}.json").write_text(
                    json.dumps(
                        {
                            "idx": idx,
                            "problem": f"problem-{idx}",
                            "answer": f"secret-reference-{idx}",
                            "subject": "test",
                            "source": "public",
                        }
                    ),
                    encoding="utf-8",
                )

            records = subset.load_selected_dataset(dataset_dir, (0, 40, 70))
            input_file = Path(temp_dir) / "input.jsonl"
            subset.write_agent_input(records, input_file)
            safe_records = [
                json.loads(line)
                for line in input_file.read_text(encoding="utf-8").splitlines()
            ]

            self.assertEqual(
                safe_records,
                [
                    {"idx": 0, "problem": "problem-0"},
                    {"idx": 40, "problem": "problem-40"},
                    {"idx": 70, "problem": "problem-70"},
                ],
            )
            self.assertNotIn("secret-reference", input_file.read_text(encoding="utf-8"))

    def test_summary_extracts_transaction_and_requires_manual_proof_review(self) -> None:
        records = [
            {
                "idx": 70,
                "problem": "证明一个环论命题。",
                "answer": "reference proof",
                "subject": "抽象代数",
            }
        ]
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)
            (output_dir / "70.json").write_text(
                json.dumps(
                    {
                        "idx": 70,
                        "status": "success",
                        "final_response": "candidate proof",
                        "trace": [
                            {
                                "step": "candidate_gate",
                                "content": {
                                    "valid_candidate_ids": ["A", "B"],
                                    "invalid_candidate_ids": [],
                                },
                            },
                            {
                                "step": "red_team_result",
                                "content": {"verdict": "ACCEPT_A"},
                            },
                            {
                                "step": "transaction_commit",
                                "content": {
                                    "candidate_id": "A",
                                    "source": "primary",
                                    "model_calls": 3,
                                    "repair_count": 0,
                                },
                            },
                        ],
                    }
                ),
                encoding="utf-8",
            )
            summary = subset.build_summary(
                records,
                output_dir,
                run_id="20260825T120000Z-hard3",
                runner_exit_code=0,
            )
            row = summary["records"][0]
            self.assertEqual(row["model_calls"], 3)
            self.assertEqual(row["selected_candidate_id"], "A")
            self.assertEqual(row["red_team_verdicts"], ["ACCEPT_A"])
            self.assertTrue(row["manual_review_required"])


if __name__ == "__main__":
    unittest.main()
