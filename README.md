# Faultline

Faultline is an incident-diagnosis lab built on the OpenTelemetry Demo. It injects known microservice faults, checks what the telemetry can prove, and later uses those misses to identify observability blind spots.

## Day 1 Status

The Day 1 environment is documented in [docs/day1-setup.md](docs/day1-setup.md).

Current foundation:

- OpenTelemetry Demo runs with Docker Compose.
- Jaeger, OpenSearch, and Prometheus are included through the demo observability stack.
- Three feature-flag faults are verified against the installed demo version:
  - `adFailure`
  - `cartFailure`
  - `paymentFailure`
- `scripts/flags.py` can list, toggle, cycle, and reset demo feature flags through the live flag API.

## Day 2 Status

The first repeatable fault-injection workflow is documented in [docs/day2-fault-injection.md](docs/day2-fault-injection.md).

Current additions:

- `cases/day2_feature_flags.json` defines 10 initial feature-flag incident cases.
- `scripts/cases.py` validates cases against the live demo, applies faults, resets flags, writes decoy change records, and captures telemetry snapshots.
- Snapshot capture records live flags, selected Prometheus metrics, recent OpenSearch logs, and a Jaeger UI reachability check.

## Day 3 Status

The telemetry tool layer is documented in [docs/day3-telemetry-tools.md](docs/day3-telemetry-tools.md).

Current additions:

- `faultline/scrubber.py` removes flagd/OpenFeature and injected-fault leakage.
- `faultline/telemetry.py` exposes tool-shaped helpers for metrics, logs, traces, dependencies, changes, and runbooks.
- `scripts/telemetry.py` provides a CLI wrapper for those tools.
- `tests/test_scrubber.py` verifies scrubbed outputs do not contain known flag names, flag-service route names, or injector terms.

## Day 4 Status

The first diagnosis agent is documented in [docs/day4-diagnosis-agent.md](docs/day4-diagnosis-agent.md).

Current additions:

- `faultline/agent.py` triages telemetry, generates hypotheses, investigates supporting signals, and returns evidence-backed conclusions.
- `scripts/diagnose.py` runs the agent against live telemetry or a saved snapshot.
- `tests/test_agent.py` verifies a corroborated diagnosis and the abstention path.

## Day 5 Status

Evidence verification is documented in [docs/day5-evidence-verification.md](docs/day5-evidence-verification.md).

Current additions:

- `faultline/verifier.py` requires at least two independent non-change telemetry signal types before a conclusion is verified.
- `faultline/eval.py` scores diagnosis JSON against known case ground truth.
- `scripts/evaluate.py` provides a CLI for evaluating saved diagnosis outputs.
- `tests/test_verifier.py` and `tests/test_eval.py` cover verification and scoring behavior.

## Day 6 Status

The evaluation harness is documented in [docs/day6-evaluation-harness.md](docs/day6-evaluation-harness.md).

Current additions:

- `faultline/harness.py` runs selected cases end-to-end and writes scored reports.
- `scripts/run_eval.py` applies cases, diagnoses live telemetry, resets flags, and scores results.
- `tests/test_harness.py` covers case selection, reset behavior, and summary writing.

## Day 7 Status

Baseline analysis is documented in [docs/day7-baseline-analysis.md](docs/day7-baseline-analysis.md).

Current additions:

- `faultline/agent.py` now uses alert-aware downstream scoring so unrelated downstream traffic does not dominate every incident.
- `faultline/analysis.py` explains incorrect evaluation results by showing whether the expected service was visible and which evidence types were missing.
- `scripts/analyze_eval.py` analyzes a saved evaluation run.
- `tests/test_analysis.py` covers miss analysis.

## Day 8 Status

Blind-spot detection is documented in [docs/day8-blind-spot-detection.md](docs/day8-blind-spot-detection.md).

Current additions:

- `faultline/blindspots.py` converts missed diagnoses into telemetry gaps and patch recommendations.
- `scripts/analyze_eval.py` now includes a `blind_spots` section with candidate patch targets and validation queries.
- `tests/test_blindspots.py` covers missing-signal and invisible-service blind spots.

## Day 9 Status

Causal ranking is documented in [docs/day9-causal-ranking.md](docs/day9-causal-ranking.md).

Current additions:

- `faultline/agent.py` records downstream causal hints when one service observes a named downstream service failing.
- Investigation now uses a causal score so internal downstream-failure evidence can outrank raw symptom volume.
- `tests/test_agent.py` covers the Day 8 payment-vs-checkout ranking miss.

## Day 10 Status

Patch planning is documented in [docs/day10-patch-plans.md](docs/day10-patch-plans.md).

Current additions:

- `faultline/patches.py` converts blind spots into concrete patch plans.
- `scripts/analyze_eval.py` output now includes `patch_plan` alongside `blind_spots`.
- `tests/test_patches.py` covers instrumentation and agent-ranking patch plans.

## Day 11 Status

Patch artifacts are documented in [docs/day11-patch-artifacts.md](docs/day11-patch-artifacts.md).

Current additions:

- `faultline/artifacts.py` renders patch plans into human-reviewable markdown.
- `scripts/write_patch_plan.py` writes `patch-plan.md` for a saved evaluation run.
- `tests/test_patch_artifacts.py` covers patch artifact rendering and writing.

## Day 12 Status

Patch bundles are documented in [docs/day12-patch-bundles.md](docs/day12-patch-bundles.md).

Current additions:

- `faultline/artifacts.py` now writes patch bundles with a markdown plan, JSON manifest, and validation script.
- `scripts/write_patch_bundle.py` creates a bundle from a saved evaluation run.
- `tests/test_patch_artifacts.py` covers manifest generation, validation script rendering, and bundle writing.

## Day 13 Status

AWS handoff artifacts are documented in [docs/day13-aws-handoff.md](docs/day13-aws-handoff.md).

Current additions:

- `faultline/aws.py` builds an AWS handoff manifest, S3 upload script, and README.
- `scripts/write_aws_handoff.py` creates AWS handoff files for a saved evaluation run.
- `tests/test_aws.py` covers AWS handoff rendering and writing.

## Quick Start

Clone the upstream demo into `vendor/`:

```sh
mkdir -p vendor
git clone https://github.com/open-telemetry/opentelemetry-demo.git vendor/opentelemetry-demo
```

Start the demo:

```sh
cd vendor/opentelemetry-demo
docker compose -f compose.yaml -f compose.full.yaml -f compose.observability.yaml up -d
```

From the Faultline repo root, inspect flags:

```sh
python3 scripts/flags.py list
```

Validate Day 2 cases:

```sh
python3 scripts/cases.py validate
```

Run Day 3 scrubber tests:

```sh
python3 -m unittest discover -s tests
```

Query scrubbed telemetry:

```sh
python3 scripts/telemetry.py list-anomalies
```

Run the Day 4 diagnosis agent:

```sh
python3 scripts/diagnose.py live --alert-service frontend --symptom checkout_errors
```

Evaluate saved diagnoses:

```sh
python3 scripts/evaluate.py results/payment-failure-100-01.json
```

Run one end-to-end evaluation case:

```sh
python3 scripts/run_eval.py --case-id payment-failure-100-01 --hold-seconds 5
```

Analyze an evaluation run:

```sh
python3 scripts/analyze_eval.py results/eval-runs/<timestamp>
```

Write a markdown patch-plan artifact:

```sh
python3 scripts/write_patch_plan.py results/eval-runs/<timestamp>
```

Write a patch bundle:

```sh
python3 scripts/write_patch_bundle.py results/eval-runs/<timestamp>
```

Write AWS handoff files:

```sh
python3 scripts/write_aws_handoff.py results/eval-runs/<timestamp>
```

Cycle the three Day 1 faults:

```sh
python3 scripts/flags.py cycle-day1 --hold-seconds 10
python3 scripts/flags.py reset
```
