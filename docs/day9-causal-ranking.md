# Faultline Day 9 Causal Ranking

Date: 2026-10-11

## Goal

Fix the Day 8 ranking ambiguity where `payment` had corroborated evidence but still lost to `checkout` because checkout had more symptom volume.

Day 9 adds:

- Causal hints in `faultline/agent.py` when a service observes a named downstream service failing.
- A causal investigation score that favors internal downstream-failure evidence over upstream symptom volume.
- Regression tests for the live Day 8 miss shape.

## What Changed

Before Day 9, the agent mostly sorted verified candidates by raw score. That made sense for obvious cases, but it had a bad failure mode:

- `checkout` accumulated many generic `POST` and checkout-alert errors.
- `payment` had direct metric and trace evidence.
- Because checkout had more volume, the agent selected checkout even when `checkout` saw `PaymentService/Charge` fail.

The agent now records `causal_hints` such as:

```text
checkout observed payment failing through oteldemo.PaymentService/Charge
```

During investigation, the agent uses a causal score:

- Internal service observing downstream failure: strong root-cause boost.
- Noisy edge service observing a service fail: smaller boost.
- Generic `GET` / `POST` symptom spans: small penalty.

This keeps `frontend -> checkout` symptoms useful while letting `checkout -> payment` evidence carry more causal weight.

## Commands

Run tests:

```sh
python3 -m unittest discover -s tests
```

Compile entrypoints:

```sh
python3 -m py_compile scripts/flags.py scripts/cases.py scripts/telemetry.py scripts/diagnose.py scripts/evaluate.py scripts/run_eval.py scripts/analyze_eval.py faultline/scrubber.py faultline/telemetry.py faultline/agent.py faultline/verifier.py faultline/eval.py faultline/harness.py faultline/analysis.py faultline/blindspots.py
```

Retry live verification when Docker is running:

```sh
python3 scripts/run_eval.py --case-id payment-failure-100-01 --hold-seconds 5
python3 scripts/flags.py list
```

## Verification Results

Ran:

```sh
python3 -m unittest discover -s tests
python3 -m py_compile scripts/flags.py scripts/cases.py scripts/telemetry.py scripts/diagnose.py scripts/evaluate.py scripts/run_eval.py scripts/analyze_eval.py faultline/scrubber.py faultline/telemetry.py faultline/agent.py faultline/verifier.py faultline/eval.py faultline/harness.py faultline/analysis.py faultline/blindspots.py
```

Results:

- Offline tests passed: 28 tests.
- Python compilation passed.
- Regression coverage now verifies that the agent selects `payment` when checkout has more symptom volume but payment has downstream causal evidence.

## Blocker

Live verification could not run because Docker was not available:

```text
failed to connect to the docker API at unix:///Users/sanjanasenthilkumar/.docker/run/docker.sock
```

Once Docker Desktop is running, rerun the live payment smoke case above. The expected result is that `payment-failure-100-01` predicts `payment` and resets `paymentFailure` to `off`.
