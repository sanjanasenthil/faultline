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

Cycle the three Day 1 faults:

```sh
python3 scripts/flags.py cycle-day1 --hold-seconds 10
python3 scripts/flags.py reset
```
