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

Cycle the three Day 1 faults:

```sh
python3 scripts/flags.py cycle-day1 --hold-seconds 10
python3 scripts/flags.py reset
```
