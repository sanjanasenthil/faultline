from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from faultline.harness import run_evaluation, select_cases


class HarnessTests(unittest.TestCase):
    def test_select_cases_by_id_and_limit(self) -> None:
        case_file = {
            "cases": [
                {"case_id": "one"},
                {"case_id": "two"},
                {"case_id": "three"},
            ]
        }

        selected = select_cases(case_file, ["three", "one"], limit=1)

        self.assertEqual([case["case_id"] for case in selected], ["one"])

    def test_select_cases_reports_unknown_id(self) -> None:
        with self.assertRaisesRegex(ValueError, "unknown case"):
            select_cases({"cases": [{"case_id": "one"}]}, ["missing"])

    def test_run_evaluation_writes_summary_and_resets(self) -> None:
        cases = [
            {
                "case_id": "payment",
                "alert": {"service": "frontend", "symptom": "checkout_errors"},
                "ground_truth": {"root_service": "payment"},
            }
        ]
        calls = []

        def apply_case(case: dict, flag_api: str, change_log: Path) -> None:
            calls.append(("apply", case["case_id"], flag_api, str(change_log)))

        def reset(flag_api: str) -> None:
            calls.append(("reset", flag_api))

        with (
            tempfile.TemporaryDirectory() as tmp,
            patch("faultline.harness.agent.collect_live_bundle", return_value={}),
            patch(
                "faultline.harness.agent.diagnose",
                return_value={
                    "conclusion": {
                        "root_service": "payment",
                        "confidence": "medium",
                        "verification": {"verified": True},
                    }
                },
            ),
        ):
            summary = run_evaluation(
                cases,
                apply_case_fn=apply_case,
                reset_fn=reset,
                flag_api="http://flag-api",
                change_log=Path(tmp) / "changes.jsonl",
                hold_seconds=0,
                prometheus_url="http://prom",
                opensearch_url="http://logs",
                jaeger_ui_url="http://jaeger",
                output_dir=Path(tmp) / "results",
            )

            self.assertEqual(summary["cases"], 1)
            self.assertEqual(summary["attempted"], 1)
            self.assertEqual(summary["correct"], 1)
            self.assertEqual(summary["errors"], [])
            self.assertTrue((Path(summary["run_dir"]) / "summary.json").exists())
            self.assertEqual(calls[0][0], "apply")
            self.assertEqual(calls[-1], ("reset", "http://flag-api"))


if __name__ == "__main__":
    unittest.main()
