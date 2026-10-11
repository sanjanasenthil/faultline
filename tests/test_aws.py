from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from faultline.aws import (
    build_aws_handoff_manifest,
    render_aws_handoff_readme,
    render_aws_upload_script,
    write_aws_handoff,
)


class AwsHandoffTests(unittest.TestCase):
    def test_builds_manifest_for_eval_run(self) -> None:
        manifest = build_aws_handoff_manifest(Path("results/eval-runs/20261010T234208Z"))

        self.assertEqual(manifest["run_id"], "20261010T234208Z")
        self.assertEqual(manifest["s3_prefix"], "faultline/eval-runs/20261010T234208Z")
        self.assertIn("results/eval-runs/20261010T234208Z/summary.json", manifest["required_files"])
        self.assertIn("S3", manifest["aws_services"][0])

    def test_renders_upload_script_with_placeholders(self) -> None:
        manifest = build_aws_handoff_manifest(Path("results/eval-runs/example"))

        script = render_aws_upload_script(manifest)

        self.assertIn("FAULTLINE_BUCKET", script)
        self.assertIn("AWS_REGION", script)
        self.assertIn("aws s3 sync", script)
        self.assertIn("faultline/eval-runs/example", script)

    def test_renders_readme(self) -> None:
        manifest = build_aws_handoff_manifest(Path("results/eval-runs/example"))

        readme = render_aws_handoff_readme(manifest)

        self.assertIn("# Faultline AWS Handoff", readme)
        self.assertIn("CodeBuild", readme)
        self.assertIn("FAULTLINE_BUCKET", readme)

    def test_writes_aws_handoff(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_dir = root / "results" / "eval-runs" / "example"
            output_dir = root / "aws-handoff"
            paths = write_aws_handoff(run_dir, output_dir)

            self.assertEqual(set(paths), {"manifest", "upload", "readme"})
            self.assertTrue(paths["manifest"].exists())
            self.assertTrue(paths["upload"].exists())
            self.assertTrue(paths["readme"].exists())
            self.assertIn("aws s3 sync", paths["upload"].read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
