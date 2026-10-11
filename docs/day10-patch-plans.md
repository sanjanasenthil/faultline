# Faultline Day 10 Patch Plans

Date: 2026-10-11

## Goal

Turn blind spots into structured patch plans.

Day 10 adds:

- `faultline/patches.py`: converts analyzer blind spots into concrete patch plans.
- `faultline/analysis.py`: includes a `patch_plan` section in analysis output.
- `tests/test_patches.py`: covers instrumentation and agent-ranking patch plans.

## What Changed

Day 8 and Day 9 explain why a diagnosis was wrong. Day 10 turns that explanation into the next engineering step.

For each blind spot, the analyzer now emits a patch plan with:

- Case ID and affected service.
- Patch kind, such as `instrumentation_logs` or `agent_ranking`.
- Priority.
- Target files.
- Implementation steps.
- Validation command or validation description.
- The original evidence gap that triggered the plan.

## Example

Run:

```sh
python3 scripts/analyze_eval.py results/eval-runs/20261010T234208Z
```

The output now includes:

```json
"patch_plan": {
  "plans": [
    {
      "kind": "agent_ranking",
      "target_files": ["faultline/agent.py"]
    },
    {
      "kind": "instrumentation_logs",
      "target_files": ["src/payment/index.js", "src/payment/charge.js", "src/payment/logger.js"]
    }
  ]
}
```

## Verification Results

Ran:

```sh
python3 -m unittest discover -s tests
python3 -m py_compile scripts/flags.py scripts/cases.py scripts/telemetry.py scripts/diagnose.py scripts/evaluate.py scripts/run_eval.py scripts/analyze_eval.py faultline/scrubber.py faultline/telemetry.py faultline/agent.py faultline/verifier.py faultline/eval.py faultline/harness.py faultline/analysis.py faultline/blindspots.py faultline/patches.py
python3 scripts/analyze_eval.py results/eval-runs/20261010T234208Z
```

Results:

- Offline tests passed.
- Python compilation passed.
- Saved evaluation analysis now includes `blind_spots` and `patch_plan`.

## Notes

This does not modify the OpenTelemetry Demo service source. The patch plan is intentionally a proposal layer first: it lets Faultline describe exactly what should be patched before applying code changes to an upstream demo checkout.
