"""First-pass diagnosis agent for Faultline incidents."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from . import telemetry
from .scrubber import assert_no_leakage, scrub


NOISY_EDGE_SERVICES = {"frontend", "frontend-proxy", "frontend-web", "load-generator"}


@dataclass
class ServiceEvidence:
    service: str
    score: float = 0.0
    metrics: list[str] = field(default_factory=list)
    traces: list[str] = field(default_factory=list)
    logs: list[str] = field(default_factory=list)
    changes: list[str] = field(default_factory=list)

    def signal_types(self) -> list[str]:
        signals = []
        if self.metrics:
            signals.append("metrics")
        if self.traces:
            signals.append("traces")
        if self.logs:
            signals.append("logs")
        if self.changes:
            signals.append("changes")
        return signals

    def to_dict(self) -> dict[str, Any]:
        return {
            "service": self.service,
            "score": round(self.score, 2),
            "signal_types": self.signal_types(),
            "metrics": self.metrics[:5],
            "traces": self.traces[:5],
            "logs": self.logs[:5],
            "changes": self.changes[:5],
        }


def _metric_results(payload: dict[str, Any], key: str | None = None) -> list[dict[str, Any]]:
    if key:
        payload = payload.get(key, {})
    return payload.get("data", {}).get("result", [])


def _value_as_float(result: dict[str, Any]) -> float:
    try:
        return float(result.get("value", [0, 0])[1])
    except (TypeError, ValueError, IndexError):
        return 0.0


def _service_from_log(hit: dict[str, Any]) -> str | None:
    source = hit.get("_source", {})
    resource = source.get("resource", {})
    service = resource.get("service.name") or source.get("service.name")
    return str(service) if service else None


def _log_body(hit: dict[str, Any]) -> str:
    source = hit.get("_source", {})
    body = str(source.get("body", "")).strip()
    severity = source.get("severity", {}).get("text")
    if severity:
        return f"{severity}: {body}"[:240]
    return body[:240]


def _candidate(candidates: dict[str, ServiceEvidence], service: str) -> ServiceEvidence:
    return candidates.setdefault(service, ServiceEvidence(service=service))


def triage(telemetry_bundle: dict[str, Any]) -> dict[str, Any]:
    anomalies = telemetry_bundle.get("anomalies", {})
    service_errors = []
    for result in _metric_results(anomalies, "service_errors"):
        service = result.get("metric", {}).get("service_name")
        if not service:
            continue
        count = _value_as_float(result)
        if count <= 0:
            continue
        service_errors.append({"service": service, "errors": count})
    service_errors.sort(key=lambda item: item["errors"], reverse=True)
    return {
        "alert": telemetry_bundle.get("alert", {"service": "frontend", "symptom": "unknown"}),
        "top_error_services": service_errors[:8],
    }


def generate_hypotheses(telemetry_bundle: dict[str, Any]) -> list[dict[str, Any]]:
    candidates: dict[str, ServiceEvidence] = {}
    anomalies = telemetry_bundle.get("anomalies", {})
    trace_summary = telemetry_bundle.get("trace_summary", {})
    logs = telemetry_bundle.get("logs", {})
    changes = telemetry_bundle.get("changes", {})

    for result in _metric_results(anomalies, "service_errors"):
        service = result.get("metric", {}).get("service_name")
        count = _value_as_float(result)
        if not service or count <= 0:
            continue
        evidence = _candidate(candidates, service)
        evidence.score += count * (0.2 if service in NOISY_EDGE_SERVICES else 1.0)
        evidence.metrics.append(f"{service} has {count:g} error spans")

    for result in _metric_results(trace_summary.get("span_calls_by_service", {})):
        metric = result.get("metric", {})
        service = metric.get("service_name")
        status_code = metric.get("status_code")
        span_name = metric.get("span_name", "unknown span")
        count = _value_as_float(result)
        if not service or status_code != "STATUS_CODE_ERROR" or count <= 0:
            continue
        evidence = _candidate(candidates, service)
        evidence.score += count * (0.15 if service in NOISY_EDGE_SERVICES else 0.75)
        evidence.traces.append(f"{span_name} returned errors {count:g} times")

    for hit in logs.get("hits", {}).get("hits", []):
        service = _service_from_log(hit)
        if not service:
            continue
        body = _log_body(hit)
        evidence = _candidate(candidates, service)
        evidence.score += 1.5
        if body:
            evidence.logs.append(body)

    for change in changes.get("changes", []):
        service = change.get("change", {}).get("service")
        if not service:
            continue
        evidence = _candidate(candidates, service)
        evidence.score += 2.0
        kind = change.get("change", {}).get("kind", "change")
        evidence.changes.append(f"recent {kind} record for {service}")

    hypotheses = [candidate.to_dict() for candidate in candidates.values()]
    hypotheses.sort(
        key=lambda item: (
            len([signal for signal in item["signal_types"] if signal != "changes"]),
            item["score"],
            item["service"] not in NOISY_EDGE_SERVICES,
        ),
        reverse=True,
    )
    return hypotheses[:8]


def investigate(hypotheses: list[dict[str, Any]]) -> dict[str, Any]:
    root_candidates = [item for item in hypotheses if item["service"] not in NOISY_EDGE_SERVICES]
    ordered = root_candidates + [item for item in hypotheses if item["service"] in NOISY_EDGE_SERVICES]
    for hypothesis in ordered:
        evidence_signals = [signal for signal in hypothesis["signal_types"] if signal != "changes"]
        if len(evidence_signals) >= 2:
            return {
                "selected_service": hypothesis["service"],
                "confidence": "medium",
                "reason": "selected because at least two non-change telemetry signals support it",
                "supporting_evidence": hypothesis,
            }
    if ordered:
        return {
            "selected_service": ordered[0]["service"],
            "confidence": "low",
            "reason": "selected from the strongest available signal, but corroboration is incomplete",
            "supporting_evidence": ordered[0],
        }
    return {
        "selected_service": None,
        "confidence": "abstain",
        "reason": "no meaningful error, trace, log, or change evidence was found",
        "supporting_evidence": {},
    }


def diagnose(telemetry_bundle: dict[str, Any]) -> dict[str, Any]:
    cleaned = scrub(telemetry_bundle)
    assert_no_leakage(cleaned)
    triage_result = triage(cleaned)
    hypotheses = generate_hypotheses(cleaned)
    investigation = investigate(hypotheses)
    result = {
        "schema_version": 1,
        "triage": triage_result,
        "hypotheses": hypotheses,
        "conclusion": {
            "root_service": investigation["selected_service"],
            "confidence": investigation["confidence"],
            "reason": investigation["reason"],
            "evidence": investigation["supporting_evidence"],
        },
        "next_steps": [
            "confirm with a fresh focused trace for the selected service",
            "compare against the known case ground truth during evaluation",
            "abstain or request more telemetry if only one signal type is present",
        ],
    }
    assert_no_leakage(result)
    return result


def collect_live_bundle(
    alert_service: str = "frontend",
    symptom: str = "unknown",
    prometheus_url: str = telemetry.DEFAULT_PROMETHEUS,
    opensearch_url: str = telemetry.DEFAULT_OPENSEARCH,
    jaeger_ui_url: str = telemetry.DEFAULT_JAEGER_UI,
    change_log: Path = telemetry.DEFAULT_CHANGE_LOG,
) -> dict[str, Any]:
    return {
        "alert": {"service": alert_service, "symptom": symptom},
        "anomalies": telemetry.list_anomalies(prometheus_url),
        "trace_summary": telemetry.get_trace_summary(prometheus_url, jaeger_ui_url),
        "dependencies": telemetry.service_dependencies(prometheus_url),
        "logs": telemetry.search_logs(size=25, opensearch_url=opensearch_url),
        "changes": telemetry.recent_changes(change_log),
    }


def load_snapshot_bundle(snapshot_dir: Path) -> dict[str, Any]:
    case = json.loads((snapshot_dir / "case.json").read_text(encoding="utf-8"))
    prometheus = json.loads((snapshot_dir / "prometheus.json").read_text(encoding="utf-8"))
    logs = json.loads((snapshot_dir / "opensearch_logs.json").read_text(encoding="utf-8"))
    alert = case.get("alert", {"service": "frontend", "symptom": "unknown"})
    return {
        "alert": alert,
        "anomalies": {
            "service_errors": prometheus.get("span_errors", {}),
            "frontend_errors": prometheus.get("frontend_errors", {}),
            "span_calls": prometheus.get("span_calls", {}),
        },
        "trace_summary": {
            "span_calls_by_service": prometheus.get("span_errors", {}),
        },
        "dependencies": {},
        "logs": logs,
        "changes": {"changes": []},
    }
