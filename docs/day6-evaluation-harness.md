# Faultline Day 6 Evaluation Harness

Date: 2026-10-10

## Goal

Turn the case catalog, injector, diagnosis agent, verifier, and scorer into a repeatable evaluation run.

Day 6 adds:

- An end-to-end harness that applies each selected case, waits for telemetry, diagnoses live evidence, resets the flags, and scores the result.
- A CLI for smoke runs and longer batch runs.
- Per-case diagnosis JSON plus a summary report under `results/eval-runs/`.

## Files

- `faultline/harness.py`: batch evaluation orchestration.
- `scripts/run_eval.py`: CLI for running selected cases.
- `tests/test_harness.py`: offline tests for case selection, reset behavior, and summary writing.
- `.gitignore`: ignores generated `results/` output.

## Commands

Run all tests:

```sh
python3 -m unittest discover -s tests
```

Run one quick smoke case:

```sh
python3 scripts/run_eval.py --case-id payment-failure-100-01 --hold-seconds 5
```

Run the first three cases:

```sh
python3 scripts/run_eval.py --limit 3 --hold-seconds 15
```

Run the full Day 2 catalog:

```sh
python3 scripts/run_eval.py --hold-seconds 30
```

## Output

Each run creates:

- `results/eval-runs/<timestamp>/diagnoses/<case_id>.json`
- `results/eval-runs/<timestamp>/summary.json`

The summary reports:

- Number of cases.
- Attempted diagnoses.
- Abstentions.
- Correct predictions.
- Accuracy on attempted cases.
- Verified conclusions.
- Per-case errors, if any.

## Safety Notes

The harness always calls reset after each case, including failure paths. It still changes live feature flags while it runs, so use `--case-id` and a short `--hold-seconds` value for smoke testing before running the full catalog.

Generated `results/`, `runs/`, and `snapshots/` output stays local and is ignored by Git.

## Verification Results

Ran:

```sh
python3 -m unittest discover -s tests
python3 -m py_compile scripts/flags.py scripts/cases.py scripts/telemetry.py scripts/diagnose.py scripts/evaluate.py scripts/run_eval.py faultline/scrubber.py faultline/telemetry.py faultline/agent.py faultline/verifier.py faultline/eval.py faultline/harness.py
python3 scripts/run_eval.py --case-id payment-failure-100-01 --hold-seconds 5
python3 scripts/flags.py list
```

Results:

- Offline tests passed.
- The one-case live smoke run wrote a diagnosis and summary under `results/eval-runs/20261010T225955Z/`.
- The smoke run correctly completed without harness errors and produced a scored result.
- The current baseline diagnosis was incorrect for that case: expected `payment`, predicted `checkout`.
- A final flag listing showed `adFailure`, `cartFailure`, and `paymentFailure` reset to `off`.

That incorrect prediction is the useful Day 6 outcome: the harness now exposes accuracy gaps instead of hiding them in manual inspection.
