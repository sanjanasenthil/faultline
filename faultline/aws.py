"""Build AWS handoff artifacts for Faultline evaluation outputs."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _posix(path: Path) -> str:
    return path.as_posix()


def build_aws_handoff_manifest(run_dir: Path, patch_bundle_dir: Path | None = None) -> dict[str, Any]:
    """Describe the local files that should be uploaded for an AWS-hosted run record."""
    bundle_dir = patch_bundle_dir or run_dir / "patch-bundle"
    run_id = run_dir.name
    return {
        "run_id": run_id,
        "run_dir": _posix(run_dir),
        "s3_prefix": f"faultline/eval-runs/{run_id}",
        "required_files": [
            _posix(run_dir / "summary.json"),
            _posix(bundle_dir / "patch-plan.md"),
            _posix(bundle_dir / "patch-manifest.json"),
            _posix(bundle_dir / "validation.sh"),
        ],
        "optional_prefixes": [
            _posix(run_dir / "diagnoses"),
            _posix(run_dir / "snapshots"),
        ],
        "aws_services": [
            "S3 for archived evaluation runs and patch bundles",
            "CodeBuild or GitHub Actions runner for scheduled evaluations",
            "CloudWatch Logs for runner output",
            "ECS or EC2 only if the OpenTelemetry Demo is later moved off local Docker",
        ],
    }


def render_aws_upload_script(manifest: dict[str, Any]) -> str:
    """Render a conservative upload script with placeholder AWS settings."""
    run_dir = manifest["run_dir"]
    s3_prefix = manifest["s3_prefix"]
    lines = [
        "#!/usr/bin/env sh",
        "set -eu",
        "",
        ': "${FAULTLINE_BUCKET:?set FAULTLINE_BUCKET to the target S3 bucket}"',
        ': "${AWS_REGION:?set AWS_REGION to the target AWS region}"',
        "",
        f'aws s3 sync "{run_dir}" "s3://${{FAULTLINE_BUCKET}}/{s3_prefix}" --region "${{AWS_REGION}}"',
        "",
        "echo \"Uploaded Faultline run to s3://${FAULTLINE_BUCKET}/" + s3_prefix + "\"",
        "",
    ]
    return "\n".join(lines)


def render_aws_handoff_readme(manifest: dict[str, Any]) -> str:
    """Render a short README for the AWS handoff directory."""
    services = "\n".join(f"- {service}" for service in manifest["aws_services"])
    required = "\n".join(f"- `{path}`" for path in manifest["required_files"])
    return "\n".join(
        [
            "# Faultline AWS Handoff",
            "",
            f"Run ID: `{manifest['run_id']}`",
            f"S3 prefix: `{manifest['s3_prefix']}`",
            "",
            "## Files To Preserve",
            "",
            required,
            "",
            "## AWS Shape",
            "",
            services,
            "",
            "## Upload",
            "",
            "Set the bucket and region, then run:",
            "",
            "```sh",
            "FAULTLINE_BUCKET=<bucket> AWS_REGION=<region> ./upload-to-s3.sh",
            "```",
            "",
            "This handoff does not create AWS resources. It packages the local run so the next step can archive it in S3 or wire it into a scheduled runner.",
            "",
        ]
    )


def write_aws_handoff(run_dir: Path, output_dir: Path | None = None, patch_bundle_dir: Path | None = None) -> dict[str, Path]:
    """Write AWS handoff files for a saved evaluation run."""
    destination = output_dir or run_dir / "aws-handoff"
    destination.mkdir(parents=True, exist_ok=True)
    manifest = build_aws_handoff_manifest(run_dir, patch_bundle_dir)

    manifest_path = destination / "aws-manifest.json"
    upload_path = destination / "upload-to-s3.sh"
    readme_path = destination / "README.md"

    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    upload_path.write_text(render_aws_upload_script(manifest), encoding="utf-8")
    upload_path.chmod(0o755)
    readme_path.write_text(render_aws_handoff_readme(manifest), encoding="utf-8")

    return {
        "manifest": manifest_path,
        "upload": upload_path,
        "readme": readme_path,
    }
