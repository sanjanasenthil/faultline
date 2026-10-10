# Faultline Day 8 Blind-Spot Detection

Date: 2026-10-10

## Goal

Turn incorrect evaluation results into concrete observability blind spots.

Day 8 adds:

- `faultline/blindspots.py`: converts miss analysis into recommended telemetry patches.
- `scripts/analyze_eval.py`: now includes a `blind_spots` section in its JSON output.
- `tests/test_blindspots.py`: covers missing-signal and invisible-service cases.

## How It Works

The Day 7 analyzer already answers: did the expected root service appear, and which evidence types did it have?

Day 8 adds the next question: what should we instrument or query next?

For each miss, the detector emits:

- The affected case and service.
- Missing signal type, such as `logs` or `traces`.
- A human-readable evidence gap.
- A recommended patch.
- Candidate source files in the OpenTelemetry Demo.
- A validation query or command to check the signal after the patch.
- Ranking ambiguity when the expected root has enough evidence but still loses to a symptom service.

## Example

For the Day 7 payment miss:

```sh
python3 scripts/analyze_eval.py results/eval-runs/20261010T231930Z
```

The analyzer reports two medium-severity blind spots:

- `payment` is missing searchable log evidence.
- `payment` is missing trace corroboration strong enough to verify it over `checkout`.

It recommends checking or patching:

- `src/payment/index.js`
- `src/payment/charge.js`
- `src/payment/logger.js`

It also gives validation commands:

```sh
python3 scripts/telemetry.py search-logs --text payment --size 10
python3 scripts/telemetry.py query-metrics 'sum by (service_name, span_name, status_code) (traces_span_metrics_calls_total{service_name="payment",status_code="STATUS_CODE_ERROR"})'
```

## Verification Results

Ran:

```sh
python3 -m unittest discover -s tests
python3 scripts/analyze_eval.py results/eval-runs/20261010T231930Z
python3 scripts/run_eval.py --case-id payment-failure-100-01 --hold-seconds 5
python3 scripts/analyze_eval.py results/eval-runs/20261010T234208Z
python3 scripts/flags.py list
```

Results:

- Offline tests passed: 25 tests.
- The saved Day 7 run now produces a `blind_spots` section.
- The payment miss is no longer just a wrong answer; it is translated into two concrete telemetry gaps with candidate patch targets and validation commands.
- A fresh live smoke run still predicted `checkout` instead of `payment`.
- In the fresh run, `payment` had `metrics` and `traces`, but no log evidence in the diagnosis bundle. The analyzer also identified a ranking ambiguity: `payment` had corroborating evidence, but `checkout` still scored higher as the symptom service.
- A final flag listing showed `paymentFailure` reset to `off`.

## Notes

The local OpenTelemetry Demo payment service already contains some logging and span error handling. That means the next fix may be a collection-window, query, or log-format issue rather than simply adding brand-new instrumentation.
