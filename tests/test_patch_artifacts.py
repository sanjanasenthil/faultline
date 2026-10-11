from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from faultline.artifacts import (
    build_patch_manifest,
    render_patch_plan_markdown,
    render_validation_script,
    write_patch_bundle,
    write_patch_plan_artifact,
)


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

    def test_builds_patch_manifest(self) -> None:
        manifest = build_patch_manifest(
            {
                "run_dir": "results/eval-runs/example",
                "patch_plan": {
                    "run_dir": "results/eval-runs/example",
                    "plans": [
                        {
                            "case_id": "payment-failure-100-01",
                            "service": "payment",
                            "kind": "instrumentation_logs",
                            "priority": "medium",
                            "target_files": ["src/payment/index.js"],
                            "validation": "rerun the case",
                            "validation_query": "python3 scripts/telemetry.py search-logs --text payment --size 10",
                        }
                    ],
                },
            }
        )

        self.assertEqual(manifest["plan_count"], 1)
        self.assertEqual(manifest["plans"][0]["service"], "payment")
        self.assertEqual(manifest["plans"][0]["target_files"], ["src/payment/index.js"])
        self.assertIn("search-logs", manifest["plans"][0]["validation_query"])

    def test_renders_validation_script(self) -> None:
        script = render_validation_script(
            {
                "plans": [
                    {
                        "validation_query": "python3 scripts/telemetry.py search-logs --text payment --size 10",
                    }
                ]
            }
        )

        self.assertIn("python3 -m unittest discover -s tests", script)
        self.assertIn("python3 scripts/telemetry.py search-logs", script)
        self.assertIn("python3 scripts/analyze_eval.py results/eval-runs/<timestamp>", script)

    def test_writes_patch_bundle(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "patch-bundle"
            paths = write_patch_bundle(
                {
                    "run_dir": str(Path(tmp) / "run"),
                    "patch_plan": {
                        "run_dir": str(Path(tmp) / "run"),
                        "plans": [
                            {
                                "case_id": "payment-failure-100-01",
                                "service": "payment",
                                "kind": "instrumentation_logs",
                                "priority": "medium",
                                "target_files": ["src/payment/index.js"],
                                "validation_query": "python3 scripts/telemetry.py search-logs --text payment --size 10",
                            }
                        ],
                    },
                },
                output_dir,
            )

            self.assertEqual(set(paths), {"plan", "manifest", "validation"})
            self.assertTrue(paths["plan"].exists())
            self.assertTrue(paths["manifest"].exists())
            self.assertTrue(paths["validation"].exists())
            self.assertIn("patch-plan.md", str(paths["plan"]))


if __name__ == "__main__":
    unittest.main()
