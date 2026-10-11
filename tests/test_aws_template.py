from __future__ import annotations

import unittest
from pathlib import Path

from scripts.validate_aws_template import validate_template


class AwsTemplateTests(unittest.TestCase):
    def test_cloudformation_template_has_required_resources(self) -> None:
        resources = validate_template(Path("infra/aws/cloudformation/faultline-mvp.json"))

        self.assertEqual(resources["ArtifactBucket"], "AWS::S3::Bucket")
        self.assertEqual(resources["BuildLogGroup"], "AWS::Logs::LogGroup")
        self.assertEqual(resources["CodeBuildRole"], "AWS::IAM::Role")
        self.assertEqual(resources["ValidationProject"], "AWS::CodeBuild::Project")

    def test_codebuild_buildspec_compiles_template_validator(self) -> None:
        buildspec = Path("infra/aws/codebuild/buildspec.yml").read_text(encoding="utf-8")

        self.assertIn("scripts/validate_aws_template.py", buildspec)
        self.assertIn("aws s3 sync", buildspec)


if __name__ == "__main__":
    unittest.main()
