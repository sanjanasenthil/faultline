# Faultline Day 1 Setup Notes

Date: 2026-10-10

## Goal

Run the OpenTelemetry Demo locally and prove that Faultline can see the three basic telemetry signals:

- Traces in Jaeger
- Logs in OpenSearch
- Metrics in Prometheus

Day 1 also needs a safe way to turn fault flags on and off.

## Repository Layout

- `vendor/opentelemetry-demo/` is a local checkout of the upstream OpenTelemetry Demo.
- `scripts/flags.py` is the project-owned helper for reading, toggling, and resetting feature-flag faults.
- `docs/day1-setup.md` records the setup and verification notes.

The upstream demo checkout is intentionally ignored by this repository so Faultline stays focused on our own automation and documentation.

## Demo Version Checked

- OpenTelemetry Demo git commit: `e5552ee2`
- Demo image version from `.env`: `3.1.0`
- Demo image tag used by compose: `latest`

## Commands

Clone the demo:

```sh
mkdir -p vendor
git clone https://github.com/open-telemetry/opentelemetry-demo.git vendor/opentelemetry-demo
```

Start the full demo plus observability stack:

```sh
cd vendor/opentelemetry-demo
docker compose -f compose.yaml -f compose.full.yaml -f compose.observability.yaml up -d
```

Find the host ports Docker assigned:

```sh
docker port jaeger
docker port opensearch
docker port frontend-proxy
docker port flagd-ui
```

On this run:

- Frontend and flag API: `http://localhost:8080`
- Prometheus: `http://localhost:9090`
- Jaeger UI: `http://localhost:56848/jaeger/ui/`
- OpenSearch: `http://localhost:56846`
- flagd-ui direct port: `http://localhost:56873`

## Feature Flags Verified Against This Demo

The live flag API confirmed these Day 1 fault flags exist:

| Flag | Day 1 variant | Meaning |
|---|---:|---|
| `adFailure` | `on` | Ad service returns failures |
| `cartFailure` | `100%` | Cart service fails all selected operations |
| `paymentFailure` | `100%` | Payment charge calls fail |

Useful commands:

```sh
python3 scripts/flags.py list
python3 scripts/flags.py set paymentFailure '100%'
python3 scripts/flags.py set paymentFailure off
python3 scripts/flags.py cycle-day1 --hold-seconds 10
python3 scripts/flags.py reset
```

The helper reads the live API first and refuses unknown flag names or variants.

Automation test result:

```sh
python3 scripts/flags.py cycle-day1 --hold-seconds 1
python3 scripts/flags.py reset
python3 scripts/flags.py list
```

Result: `adFailure`, `cartFailure`, and `paymentFailure` each enabled successfully, then returned to `off`. A final list check showed every live flag default back at `off`.

## Verification Results

OpenSearch logs:

```sh
curl 'http://localhost:56846/_cat/indices?v'
```

Result: `otel-logs-2026-10-10` existed with 844 log documents on the first check. A later document search returned 1,937 total log documents and showed a Kafka log record with `service.name: kafka`.

Prometheus metrics:

```sh
curl 'http://localhost:9090/api/v1/label/__name__/values'
curl 'http://localhost:9090/api/v1/query?query=demo_ad_requests_total'
curl 'http://localhost:9090/api/v1/query?query=otelcol_exporter_sent_spans_total'
```

Results:

- Prometheus had many demo metric names, including `demo_ad_requests_total`, `http_server_request_duration_seconds_*`, and `traces_span_metrics_calls_total`.
- `demo_ad_requests_total` returned a sample for `service_name="ad"` with value `3`.
- `otelcol_exporter_sent_spans_total` showed spans exported to Jaeger storage, including `jaeger_storage_exporter=2234` and `otlp_grpc/jaeger=2051`.

Jaeger traces:

```sh
curl 'http://localhost:56848/jaeger/ui/'
```

Result: Jaeger UI returned HTTP 200. The older JSON endpoint `/api/services` returned HTTP 404 in Jaeger `2.21.0`, so the concrete trace ingestion proof for this version is the Prometheus span-export metric above plus the working Jaeger UI.

Flag API:

```sh
curl 'http://localhost:8080/feature/api/read'
```

Result: returned the live flag config with all Day 1 flags present.

## Current Blockers / Notes

- The local sandbox cannot directly reach Docker-published localhost ports; host-network checks need normal host access.
- Jaeger `2.21.0` in this demo serves the UI at `/jaeger/ui/`, but the old `/api/services` route returns 404. Use the UI plus exporter metrics for Day 1 verification, or add a Jaeger v2-compatible query method on Day 2.
- Most compose ports are random host ports except frontend-proxy (`8080`), Envoy admin (`10000`), and Prometheus (`9090`). Re-run `docker port ...` after restarting the stack.
- `git init` at the project mirror root was blocked by local filesystem permissions on `.git`, so the GitHub repository was cloned into `faultline/` as the real Git checkout.

## Learning Notes

Docker Compose starts the shop services and the telemetry services as one local system. The app emits telemetry to the OpenTelemetry Collector. The collector sends traces to Jaeger, logs to OpenSearch, and metrics to Prometheus. Faultline will eventually sit beside those systems: it will inject a known fault, observe the telemetry, and ask whether the available evidence is enough to diagnose the real root cause.
