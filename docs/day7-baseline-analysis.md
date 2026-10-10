# Faultline Day 7 Baseline Analysis

Date: 2026-10-10

## Goal

Use the Day 6 evaluation harness to measure the current diagnosis loop, then turn misses into concrete observability feedback.

Day 7 adds:

- Alert-aware downstream scoring in `faultline/agent.py`.
- A miss-analysis helper in `faultline/analysis.py`.
- A CLI for explaining evaluation misses with `scripts/analyze_eval.py`.
- Regression tests for the checkout/payment miss pattern.

## What Changed

The first Day 7 live run exposed a false positive: unrelated product-catalog traffic dominated a checkout alert because the agent credited every downstream error span equally.

The agent now:

- Extracts downstream demo service names from spans like `oteldemo.PaymentService/Charge`.
- Keeps more hypotheses so lower-volume root-service candidates are still visible.
- Applies alert-symptom filtering before giving large downstream credit. For example, `product-catalog` can still matter for homepage or recommendation alerts, but it no longer overwhelms checkout/payment incidents.

The analyzer reports missed cases by comparing:

- Expected root service from the case catalog.
- Predicted root service from the diagnosis.
- Whether the expected service appeared at all.
- Which independent evidence types were present or missing for the expected service.

## Commands

Run all tests:

```sh
python3 -m unittest discover -s tests
```

Compile the Python entrypoints:

```sh
python3 -m py_compile scripts/flags.py scripts/cases.py scripts/telemetry.py scripts/diagnose.py scripts/evaluate.py scripts/run_eval.py scripts/analyze_eval.py faultline/scrubber.py faultline/telemetry.py faultline/agent.py faultline/verifier.py faultline/eval.py faultline/harness.py faultline/analysis.py
```

Run the live payment smoke case:

```sh
python3 scripts/run_eval.py --case-id payment-failure-100-01 --hold-seconds 5
```

Analyze a run:

```sh
python3 scripts/analyze_eval.py results/eval-runs/<timestamp>
```

## Verification Results

Ran:

```sh
python3 -m unittest discover -s tests
python3 -m py_compile scripts/flags.py scripts/cases.py scripts/telemetry.py scripts/diagnose.py scripts/evaluate.py scripts/run_eval.py scripts/analyze_eval.py faultline/scrubber.py faultline/telemetry.py faultline/agent.py faultline/verifier.py faultline/eval.py faultline/harness.py faultline/analysis.py
python3 scripts/run_eval.py --case-id payment-failure-100-01 --hold-seconds 5
python3 scripts/analyze_eval.py results/eval-runs/20261010T231930Z
python3 scripts/flags.py list
```

Results:

- Offline tests passed: 23 tests.
- Python compilation passed.
- The live run completed and reset feature flags.
- The product-catalog false positive was removed.
- The remaining baseline miss is now explicit: expected `payment`, predicted `checkout`.
- The analyzer found that `payment` was visible through `metrics`, but missing independent `logs` and `traces` evidence in the collected window. `checkout` had both `metrics` and `traces`, so the verifier selected it.

## Blocker

The current telemetry bundle does not provide enough corroborating evidence for `payment` during the short `paymentFailure=100%` smoke run. The diagnosis agent should not claim a verified payment root from one signal type alone.

That is the right next observability task: add a focused trace/log query around checkout-to-payment calls, or improve demo instrumentation so payment failures produce direct trace/log evidence that survives the scrubber.
