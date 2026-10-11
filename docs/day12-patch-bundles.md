# Faultline Day 12 Patch Bundles

Date: 2026-10-11

## Goal

Package patch plans into apply-ready bundles.

Day 12 adds:

- `write_patch_bundle` in `faultline/artifacts.py`: writes a small patch bundle directory.
- `scripts/write_patch_bundle.py`: creates the bundle from a saved evaluation run.
- More artifact tests for manifest generation, validation script rendering, and bundle writing.

## What Changed

Day 11 produced a readable `patch-plan.md`. Day 12 writes the patch plan alongside two extra files:

- `patch-manifest.json`: a compact machine-readable summary of every planned patch.
- `validation.sh`: the checks to run after applying the patch, including tests and any telemetry validation queries.

This keeps the workflow deliberate:

1. Analyze the run.
2. Generate a patch plan.
3. Generate a patch bundle.
4. Apply one patch.
5. Run validation.
6. Re-run the evaluation and compare results.

## Usage

Run:

```sh
python3 scripts/write_patch_bundle.py results/eval-runs/<timestamp>
```

By default, this writes:

```text
results/eval-runs/<timestamp>/patch-bundle/patch-plan.md
results/eval-runs/<timestamp>/patch-bundle/patch-manifest.json
results/eval-runs/<timestamp>/patch-bundle/validation.sh
```

The bundle is written under `results/`, which is ignored by git.

## Verification Results

Ran:

```sh
python3 -m unittest discover -s tests
python3 -m py_compile scripts/flags.py scripts/cases.py scripts/telemetry.py scripts/diagnose.py scripts/evaluate.py scripts/run_eval.py scripts/analyze_eval.py scripts/write_patch_plan.py scripts/write_patch_bundle.py faultline/scrubber.py faultline/telemetry.py faultline/agent.py faultline/verifier.py faultline/eval.py faultline/harness.py faultline/analysis.py faultline/blindspots.py faultline/patches.py faultline/artifacts.py
python3 scripts/write_patch_bundle.py results/eval-runs/20261010T234208Z
```

Expected result:

- Offline tests pass.
- Python compilation passes.
- A patch bundle is written under the saved run directory.

## Notes

This still does not edit the OpenTelemetry Demo service files. The next measured step is to apply one planned patch, preferably the payment logging patch, then rerun the matching case and compare the analyzer output.
