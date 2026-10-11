# Faultline Day 13 AWS Handoff

Date: 2026-10-11

## Goal

Prepare Faultline outputs for AWS without creating cloud resources yet.

Day 13 adds:

- `faultline/aws.py`: builds an AWS handoff manifest, upload script, and README.
- `scripts/write_aws_handoff.py`: creates the handoff files for a saved evaluation run.
- `tests/test_aws.py`: covers manifest generation, upload script rendering, README rendering, and file writing.

## What Changed

The local workflow now has a clean AWS handoff point. After an evaluation run and patch bundle exist, Faultline can write:

- `aws-manifest.json`: run ID, S3 prefix, important files, optional directories, and suggested AWS services.
- `upload-to-s3.sh`: a conservative S3 sync command that requires `FAULTLINE_BUCKET` and `AWS_REGION`.
- `README.md`: short instructions for preserving the run in AWS.

This keeps AWS work separated from local diagnosis work. Nothing is deployed automatically, and no credentials are required to generate the handoff files.

## Usage

Run:

```sh
python3 scripts/write_aws_handoff.py results/eval-runs/<timestamp>
```

By default, this writes:

```text
results/eval-runs/<timestamp>/aws-handoff/aws-manifest.json
results/eval-runs/<timestamp>/aws-handoff/upload-to-s3.sh
results/eval-runs/<timestamp>/aws-handoff/README.md
```

To upload later:

```sh
FAULTLINE_BUCKET=<bucket> AWS_REGION=<region> results/eval-runs/<timestamp>/aws-handoff/upload-to-s3.sh
```

## Suggested AWS Shape

- S3 stores evaluation runs, diagnoses, patch bundles, and handoff manifests.
- CodeBuild or a GitHub Actions runner can run scheduled evaluations.
- CloudWatch Logs captures runner output.
- ECS or EC2 is only needed if the OpenTelemetry Demo moves from local Docker into AWS.

## Verification Results

Ran:

```sh
python3 -m unittest discover -s tests
python3 -m py_compile scripts/flags.py scripts/cases.py scripts/telemetry.py scripts/diagnose.py scripts/evaluate.py scripts/run_eval.py scripts/analyze_eval.py scripts/write_patch_plan.py scripts/write_patch_bundle.py scripts/write_aws_handoff.py faultline/scrubber.py faultline/telemetry.py faultline/agent.py faultline/verifier.py faultline/eval.py faultline/harness.py faultline/analysis.py faultline/blindspots.py faultline/patches.py faultline/artifacts.py faultline/aws.py
python3 scripts/write_aws_handoff.py results/eval-runs/20261010T234208Z
```

Expected result:

- Offline tests pass.
- Python compilation passes.
- AWS handoff files are written under the saved run directory.

## Notes

This is the first AWS-facing piece. It does not provision S3, IAM, CodeBuild, ECS, or EC2. That is intentional: the project now has a clear artifact boundary before cloud deployment.
