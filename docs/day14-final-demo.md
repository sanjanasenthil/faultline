# Faultline Day 14 Final Demo

Date: 2026-10-11

## Goal

Package the 14-day MVP into a final demo report.

Day 14 adds:

- `faultline/report.py`: renders a final demo report from an analyzed evaluation run.
- `scripts/write_demo_report.py`: writes `final-demo-report.md` for a saved run.
- `tests/test_report.py`: covers report rendering and writing.

## What Changed

The project now has a concise final artifact that explains:

- The MVP loop.
- Evaluation results.
- Misses and patch evidence.
- Patch bundle files.
- AWS deployment status.
- Verification commands.
- Remaining blockers.
- A suggested demo script.

## Usage

Run:

```sh
python3 scripts/write_demo_report.py results/eval-runs/<timestamp>
```

By default, this writes:

```text
results/eval-runs/<timestamp>/final-report/final-demo-report.md
```

## Verification Results

Ran:

```sh
python3 -m unittest discover -s tests
python3 -m py_compile scripts/flags.py scripts/cases.py scripts/telemetry.py scripts/diagnose.py scripts/evaluate.py scripts/run_eval.py scripts/analyze_eval.py scripts/write_patch_plan.py scripts/write_patch_bundle.py scripts/write_aws_handoff.py scripts/write_demo_report.py scripts/validate_aws_template.py faultline/scrubber.py faultline/telemetry.py faultline/agent.py faultline/verifier.py faultline/eval.py faultline/harness.py faultline/analysis.py faultline/blindspots.py faultline/patches.py faultline/artifacts.py faultline/aws.py faultline/report.py
python3 scripts/write_demo_report.py results/eval-runs/20261010T234208Z
python3 scripts/validate_aws_template.py
```

Expected result:

- Offline tests pass.
- Python compilation passes.
- A final demo report is written under the saved run directory.

## Notes

This closes the 14-day MVP with an AWS deployment path. The validation layer can run on AWS CodeBuild and store artifacts in S3; moving the full OpenTelemetry Demo to ECS or EC2 remains a future extension.
