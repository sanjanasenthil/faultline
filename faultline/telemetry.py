"""Telemetry tool functions for Faultline.

These functions are intentionally dependency-light. They are shaped like the
future MCP tools, while remaining easy to test and run from a normal terminal.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

from .scrubber import scrub


DEFAULT_PROMETHEUS = "http://localhost:9090"
DEFAULT_OPENSEARCH = "http://localhost:56846"
DEFAULT_JAEGER_UI = "http://localhost:56848/jaeger/ui/"
DEFAULT_CHANGE_LOG = Path("runs/change-log.jsonl")


def request_json(method: str, url: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    data = None
    headers = {}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=20) as response:
            body = response.read().decode("utf-8")
    except urllib.error.URLError as exc:
        raise RuntimeError(f"request failed for {url}: {exc}") from exc
    return json.loads(body) if body else {}


def query_metrics(query: str, prometheus_url: str = DEFAULT_PROMETHEUS, should_scrub: bool = True) -> dict[str, Any]:
    params = urllib.parse.urlencode({"query": query})
    payload = request_json("GET", f"{prometheus_url}/api/v1/query?{params}")
    return scrub(payload) if should_scrub else payload


def list_anomalies(prometheus_url: str = DEFAULT_PROMETHEUS, should_scrub: bool = True) -> dict[str, Any]:
    queries = {
        "frontend_errors": "traces_span_metrics_calls_total{service_name=\"frontend\",status_code=\"STATUS_CODE_ERROR\"}",
        "service_errors": "sum by (service_name) (traces_span_metrics_calls_total{status_code=\"STATUS_CODE_ERROR\"})",
        "span_calls": "sum by (service_name) (traces_span_metrics_calls_total)",
        "otel_exported_spans": "otelcol_exporter_sent_spans_total",
    }
    result = {name: query_metrics(query, prometheus_url, should_scrub=False) for name, query in queries.items()}
    return scrub(result) if should_scrub else result


def search_logs(
    text: str | None = None,
    size: int = 20,
    opensearch_url: str = DEFAULT_OPENSEARCH,
    should_scrub: bool = True,
) -> dict[str, Any]:
    query: dict[str, Any]
    if text:
        query = {"multi_match": {"query": text, "fields": ["body", "severity.text", "resource.service.name"]}}
    else:
        query = {"match_all": {}}
    payload = {
        "size": size,
        "sort": [{"@timestamp": {"order": "desc"}}],
        "query": query,
    }
    result = request_json("POST", f"{opensearch_url}/otel-logs-*/_search", payload)
    return scrub(result) if should_scrub else result


def get_trace_summary(prometheus_url: str = DEFAULT_PROMETHEUS, jaeger_ui_url: str = DEFAULT_JAEGER_UI, should_scrub: bool = True) -> dict[str, Any]:
    """Return machine-readable trace-derived metrics plus the Jaeger UI location."""

    payload = {
        "jaeger_ui": jaeger_ui_url,
        "span_calls_by_service": query_metrics(
            "sum by (service_name, span_name, status_code) (traces_span_metrics_calls_total)",
            prometheus_url,
            should_scrub=False,
        ),
    }
    return scrub(payload) if should_scrub else payload


def service_dependencies(prometheus_url: str = DEFAULT_PROMETHEUS, should_scrub: bool = True) -> dict[str, Any]:
    """Return a dependency-oriented view based on client span names.

    The OpenTelemetry Demo's current Jaeger API path is not JSON-friendly in this
    setup, so this derives a useful service/span map from Prometheus span metrics.
    """

    payload = query_metrics(
        "sum by (service_name, span_name) (traces_span_metrics_calls_total{span_kind=\"SPAN_KIND_CLIENT\"})",
        prometheus_url,
        should_scrub=False,
    )
    return scrub(payload) if should_scrub else payload


def recent_changes(change_log: Path = DEFAULT_CHANGE_LOG, limit: int = 20, should_scrub: bool = True) -> dict[str, Any]:
    if not change_log.exists():
        return {"changes": []}
    lines = change_log.read_text(encoding="utf-8").splitlines()
    records = [json.loads(line) for line in lines if line.strip()]
    payload = {"changes": records[-limit:]}
    return scrub(payload) if should_scrub else payload


def search_runbooks(query: str) -> dict[str, Any]:
    """Placeholder runbook search for the Day 3 tool contract."""

    return {
        "query": query,
        "matches": [
            {
                "title": "Use traces first, then corroborate with logs and metrics",
                "body": "Prefer root-cause evidence from upstream/downstream span status, then confirm with service logs or Prometheus counters.",
            }
        ],
    }
