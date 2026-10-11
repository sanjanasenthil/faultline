from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from faultline.report import render_demo_report, write_demo_report


class DemoReportTests(unittest.TestCase):
    def test_renders_final_demo_report(self) -> None:
        report = render_demo_report(
            {
                "run_dir": "results/eval-runs/example",
                "cases": 1,
                "attempted": 1,
                "correct": 0,
                "accuracy_on_attempted": 0.0,
                "misses": [
                    {
                        "case_id": "payment-failure-100-01",
                        "expected_root_service": "payment",
                        "predicted_root_service": "checkout",
                    }
                ],
                "patch_plan": {
                    "plans": [
                        {
                            "kind": "instrumentation_logs",
                            "service": "payment",
                            "target_files": ["src/payment/index.js"],
                        }
                    ]
                },
            }
        )

        self.assertIn("# Faultline Final Demo Report", report)
        self.assertIn("expected `payment`, predicted `checkout`", report)
        self.assertIn("AWS is required", report)
        self.assertIn("Demo Script", report)

    def test_writes_final_demo_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = write_demo_report(
                {
                    "run_dir": str(Path(tmp) / "run"),
                    "cases": 0,
                    "attempted": 0,
                    "correct": 0,
                    "accuracy_on_attempted": None,
                    "misses": [],
                    "patch_plan": {"plans": []},
                },
                Path(tmp) / "report",
            )

            self.assertEqual(path.name, "final-demo-report.md")
            self.assertTrue(path.exists())
            self.assertIn("Faultline Final Demo Report", path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
