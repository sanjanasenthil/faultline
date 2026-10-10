from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from faultline.analysis import analyze_run


class AnalysisTests(unittest.TestCase):
    def test_reports_missing_expected_service_corroboration_for_miss(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            cases = root / "cases.json"
            run_dir = root / "run"
            diagnoses = run_dir / "diagnoses"
            diagnoses.mkdir(parents=True)
            cases.write_text(
                json.dumps(
                    {
                        "cases": [
                            {
                                "case_id": "payment-failure-100-01",
                                "alert": {"service": "frontend", "symptom": "checkout_errors"},
                                "ground_truth": {"root_service": "payment"},
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            (run_dir / "summary.json").write_text(
                json.dumps(
                    {
                        "cases": 1,
                        "attempted": 1,
                        "correct": 0,
                        "accuracy_on_attempted": 0.0,
                        "scores": [
                            {
                                "case_id": "payment-failure-100-01",
                                "expected_root_service": "payment",
                                "predicted_root_service": "checkout",
                                "verified": True,
                                "correct": False,
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            (diagnoses / "payment-failure-100-01.json").write_text(
                json.dumps(
                    {
                        "hypotheses": [
                            {"service": "checkout", "signal_types": ["metrics", "traces"]},
                            {"service": "payment", "signal_types": ["metrics"]},
                        ]
                    }
                ),
                encoding="utf-8",
            )

            report = analyze_run(run_dir, cases)

        self.assertEqual(report["misses"][0]["expected_root_service"], "payment")
        self.assertEqual(report["misses"][0]["expected_signal_types"], ["metrics"])
        self.assertEqual(report["misses"][0]["expected_missing_signal_types"], ["logs", "traces"])


if __name__ == "__main__":
    unittest.main()
