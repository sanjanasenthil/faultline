# Faultline Project Overview

Faultline is an incident-diagnosis lab built on the OpenTelemetry Demo. It injects known microservice faults, collects telemetry, asks a diagnosis agent to find the root cause, checks whether the diagnosis is supported by evidence, and turns missed diagnoses into observability patch plans.

The main idea is a closed improvement loop:

```text
Inject fault -> Diagnose -> Verify evidence -> Find blind spots -> Plan patches -> Re-test
```

## What Faultline Demonstrates

Faultline is not just an AI incident-response demo. It measures whether the diagnosis was correct and then explains what telemetry was missing when the diagnosis failed.

The MVP includes:

- Feature-flag fault injection for OpenTelemetry Demo services.
- Telemetry tools for metrics, logs, traces, dependencies, changes, and runbooks.
- A diagnosis agent that forms hypotheses from telemetry.
- Evidence verification that requires multiple independent signal types.
- An evaluation harness for known fault cases.
- Blind-spot detection for missed diagnoses.
- Patch plans and patch bundles for improving instrumentation.
- AWS deployment artifacts for running validation in CodeBuild and storing proof artifacts in S3.
- A final demo report generator.

## Core Workflow

1. Define a known incident case in `cases/day2_feature_flags.json`.
2. Apply the fault with `scripts/run_eval.py`.
3. Diagnose the incident from telemetry.
4. Score the diagnosis against ground truth.
5. Analyze misses with `scripts/analyze_eval.py`.
6. Generate patch artifacts with `scripts/write_patch_bundle.py`.
7. Prepare AWS proof artifacts with `scripts/write_aws_handoff.py`.
8. Generate the final report with `scripts/write_demo_report.py`.

## AWS Deployment Path

AWS is part of the project requirement. The repository includes a deployable AWS validation layer:

- `infra/aws/cloudformation/faultline-mvp.json` creates S3, CloudWatch Logs, IAM, and CodeBuild resources.
- `infra/aws/codebuild/buildspec.yml` runs the Faultline test and compile checks inside AWS CodeBuild.
- `docs/aws-deployment.md` explains deployment, proof, and cleanup.
- `scripts/validate_aws_template.py` checks the local CloudFormation template shape before deployment.

The AWS MVP proves that Faultline can run validation in AWS and store artifacts in S3. Running the full OpenTelemetry Demo on ECS or EC2 is a future extension.

## Current MVP Status

The 14-day MVP is complete as a local plus AWS-validation project.

Verified locally:

- Unit test suite passes.
- Python compile checks pass.
- AWS CloudFormation template shape validates locally.
- Saved evaluation run can produce patch bundles, AWS handoff files, and a final demo report.

Known limitations:

- Live Docker verification depends on Docker being available locally.
- AWS deployment requires AWS CLI and credentials.
- The AWS stack runs validation in CodeBuild; it does not yet host the full OpenTelemetry Demo.

## Demo Story

The recommended demo flow is:

1. Show the fault case catalog.
2. Show the evaluation harness.
3. Show the saved run summary and diagnosis.
4. Analyze the miss and blind spots.
5. Show the generated patch bundle.
6. Show the AWS CloudFormation stack and CodeBuild buildspec.
7. Show the final demo report.

The strongest project claim is:

Faultline does not stop at “the AI guessed a root cause.” It checks the diagnosis against evidence, identifies missing telemetry, and produces the next patch needed to make future diagnoses better.
