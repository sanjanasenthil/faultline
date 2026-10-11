#!/usr/bin/env python3
"""Validate the local AWS CloudFormation template shape."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


REQUIRED_RESOURCES = {
    "ArtifactBucket": "AWS::S3::Bucket",
    "BuildLogGroup": "AWS::Logs::LogGroup",
    "CodeBuildRole": "AWS::IAM::Role",
    "ValidationProject": "AWS::CodeBuild::Project",
}


def validate_template(path: Path) -> dict[str, str]:
    template = json.loads(path.read_text(encoding="utf-8"))
    resources = template.get("Resources", {})
    missing = {
        name: resource_type
        for name, resource_type in REQUIRED_RESOURCES.items()
        if resources.get(name, {}).get("Type") != resource_type
    }
    if missing:
        missing_text = ", ".join(f"{name} ({resource_type})" for name, resource_type in missing.items())
        raise ValueError(f"missing required resources: {missing_text}")
    project = resources["ValidationProject"]["Properties"]
    if not project.get("Environment", {}).get("PrivilegedMode"):
        raise ValueError("ValidationProject must enable privileged Docker mode")
    return {name: resources[name]["Type"] for name in REQUIRED_RESOURCES}


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Faultline's AWS CloudFormation template.")
    parser.add_argument(
        "template",
        type=Path,
        nargs="?",
        default=Path("infra/aws/cloudformation/faultline-mvp.json"),
    )
    args = parser.parse_args()

    resources = validate_template(args.template)
    for name, resource_type in resources.items():
        print(f"{name}: {resource_type}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
