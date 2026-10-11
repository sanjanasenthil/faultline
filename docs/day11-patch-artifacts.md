# Faultline Day 11 Patch Artifacts

Date: 2026-10-11

## Goal

Turn structured patch plans into a reviewable artifact.

Day 11 adds:

- `faultline/artifacts.py`: renders patch plans as markdown and writes them to disk.
- `scripts/write_patch_plan.py`: creates `patch-plan.md` for a saved evaluation run.
- `tests/test_patch_artifacts.py`: covers the renderer and writer.

## What Changed

Day 10 generated machine-readable patch plans. Day 11 writes those plans into a markdown file that is easier to review before changing service code.

The artifact includes:

- Evaluation run path.
- Number of patch plans.
- Case ID, service, priority, and objective for each plan.
- Source evidence gap.
- Target files.
- Implementation steps.
- Validation instructions or validation query.

## Usage

Run:

```sh
python3 scripts/write_patch_plan.py results/eval-runs/<timestamp>
```

By default, this writes:

```text
results/eval-runs/<timestamp>/patch-plan/patch-plan.md
```

The `results/` directory is ignored by git, so generated run artifacts stay local.

To write somewhere else:

```sh
python3 scripts/write_patch_plan.py results/eval-runs/<timestamp> --output-dir /tmp/faultline-patch-plan
```

## Verification Results

Ran:

```sh
python3 -m unittest discover -s tests
python3 -m py_compile scripts/flags.py scripts/cases.py scripts/telemetry.py scripts/diagnose.py scripts/evaluate.py scripts/run_eval.py scripts/analyze_eval.py scripts/write_patch_plan.py faultline/scrubber.py faultline/telemetry.py faultline/agent.py faultline/verifier.py faultline/eval.py faultline/harness.py faultline/analysis.py faultline/blindspots.py faultline/patches.py faultline/artifacts.py
python3 scripts/write_patch_plan.py results/eval-runs/20261010T234208Z
```

Expected result:

- Offline tests pass.
- Python compilation passes.
- `patch-plan.md` is written under the saved run directory.

## Notes

This still does not modify the OpenTelemetry Demo source. It prepares a concrete review artifact so the next step can apply one patch deliberately and then measure whether diagnosis accuracy improves.
