# Faultline Day 5 Evidence Verification

Date: 2026-10-10

## Goal

Make diagnosis evidence explicit, testable, and measurable.

Day 5 adds:

- A verifier that requires at least two independent telemetry signal types before a diagnosis is considered verified.
- Decoy-aware handling: recent change records are useful context but do not count as proof.
- Evaluation helpers for scoring saved diagnosis JSON against the Day 2 case ground truth.

## Files

- `faultline/verifier.py`: evidence verification rules.
- `faultline/eval.py`: scoring helpers for case-level evaluation.
- `scripts/evaluate.py`: CLI for scoring diagnosis JSON files.
- `tests/test_verifier.py`: verifier tests.
- `tests/test_eval.py`: evaluation tests.

## Commands

Run all tests:

```sh
python3 -m unittest discover -s tests
```

Run a live diagnosis:

```sh
python3 scripts/diagnose.py live --alert-service frontend --symptom checkout_errors
```

Evaluate saved diagnosis files:

```sh
python3 scripts/evaluate.py results/payment-failure-100-01.json
```

The evaluator expects each diagnosis JSON file to either include a top-level `case_id`, or have a filename stem that matches a case ID from `cases/day2_feature_flags.json`.

## Verification Rule

A conclusion is verified only when it has:

- A candidate service.
- At least two non-change signal types from metrics, traces, or logs.

Recent changes are excluded from proof because Day 2 introduced decoy deploy records. A diagnosis may mention a recent change, but it must still stand on telemetry evidence.

## Verification Results

Ran:

```sh
python3 -m unittest discover -s tests
python3 -m py_compile scripts/flags.py scripts/cases.py scripts/telemetry.py scripts/diagnose.py scripts/evaluate.py faultline/scrubber.py faultline/telemetry.py faultline/agent.py faultline/verifier.py faultline/eval.py
```

Results:

- Verifier, agent, scrubber, and evaluation tests passed.
- Agent conclusions now include a `verification` object with independent signal types and pass/fail status.
- Change-only evidence correctly fails verification.
- A live `frontend` / `checkout_errors` diagnosis selected `checkout` with verified `metrics` and `traces` evidence.
- The live smoke test exposed a ranking issue where a tiny three-signal candidate could beat a stronger two-signal candidate; selection now uses verification as a gate and score as the tiebreaker for downstream services.

## Current Limit

The evaluator scores saved diagnosis files. It does not yet batch-run all cases end-to-end by injecting each fault, waiting, diagnosing, and resetting. That belongs in the Day 6 evaluation harness.
