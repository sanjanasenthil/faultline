# Faultline Day 3 Telemetry Tools

Date: 2026-10-10

## Goal

Expose telemetry through a small, testable tool layer and prevent anti-cheating leaks before the diagnosis agent exists.

Day 3 adds:

- Scrubbed telemetry helpers for metrics, logs, traces, service dependencies, recent changes, and runbooks.
- A CLI wrapper that mirrors the future MCP tool surface.
- Leakage tests that fail if flag names, flagd spans, or injector labels survive scrubbing.

## Files

- `faultline/scrubber.py`: removes flagd/OpenFeature records and redacts injected fault names.
- `faultline/telemetry.py`: tool functions for Prometheus, OpenSearch, trace summaries, dependency summaries, recent changes, and runbook lookup.
- `scripts/telemetry.py`: command-line wrapper for the tool functions.
- `tests/test_scrubber.py`: unit tests for the anti-cheating scrubber.

## Tool Commands

List anomaly-oriented metrics:

```sh
python3 scripts/telemetry.py list-anomalies
```

Query a Prometheus expression:

```sh
python3 scripts/telemetry.py query-metrics 'sum by (service_name) (traces_span_metrics_calls_total)'
```

Search recent logs:

```sh
python3 scripts/telemetry.py search-logs --text checkout --size 5
```

Get trace-derived summary data:

```sh
python3 scripts/telemetry.py get-trace
```

Get client-span dependency hints:

```sh
python3 scripts/telemetry.py service-dependencies
```

Read decoy changes:

```sh
python3 scripts/telemetry.py recent-changes
```

Search starter runbook text:

```sh
python3 scripts/telemetry.py search-runbooks checkout
```

## Verification Results

Ran:

```sh
python3 -m unittest discover -s tests
python3 scripts/telemetry.py list-anomalies
python3 scripts/telemetry.py search-logs --text checkout --size 3
python3 scripts/telemetry.py service-dependencies
```

Results:

- Scrubber tests passed.
- Live telemetry commands returned data from the running demo.
- Scrubbed outputs passed `assert_no_leakage`, meaning known flag names, `flagd`, OpenFeature terms, and injector labels were absent from tool output.
- A live dependency check exposed `router flagservice egress`; the scrubber now redacts `flagservice` and has a regression test for that route-name leak.

## Current Limit

This is not a full MCP server process yet. It is the tool contract and scrubbed implementation that a server can wrap next. This is intentional: the risky part on Day 3 is the telemetry boundary and anti-cheating behavior, so those are tested first.
