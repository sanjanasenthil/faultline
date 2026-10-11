from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from faultline.artifacts import render_patch_plan_markdown, write_patch_plan_artifact


class PatchArtifactTests(unittest.TestCase):
    def test_renders_patch_plan_markdown(self) -> None:
        markdown = render_patch_plan_markdown(
            {
                "run_dir": "results/eval-runs/example",
                "plans": [
                    {
                        "case_id": "payment-failure-100-01",
                        "service": "payment",
                        "kind": "instrumentation_logs",
                        "priority": "medium",
                        "objective": "Make service failures searchable in OpenSearch.",
                        "source_gap": "payment logs were missing",
                        "target_files": ["src/payment/index.js"],
                        "steps": ["add structured error logs"],
                        "validation": "rerun the case",
                        "validation_query": "python3 scripts/telemetry.py search-logs --text payment --size 10",
                    }
                ],
            }
        )

        self.assertIn("# Faultline Patch Plan", markdown)
        self.assertIn("- Run: `results/eval-runs/example`", markdown)
        self.assertIn("## 1. instrumentation_logs", markdown)
        self.assertIn("src/payment/index.js", markdown)
        self.assertIn("python3 scripts/telemetry.py search-logs", markdown)

    def test_writes_patch_plan_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "patch-plan"
            path = write_patch_plan_artifact(
                {
                    "run_dir": str(Path(tmp) / "run"),
                    "patch_plan": {
                        "run_dir": str(Path(tmp) / "run"),
                        "plans": [],
                    },
                },
                output_dir,
            )

            self.assertEqual(path, output_dir / "patch-plan.md")
            self.assertTrue(path.exists())
            self.assertIn("No patch plans", path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
