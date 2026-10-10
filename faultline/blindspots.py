"""Convert diagnosis misses into observability blind spots."""

from __future__ import annotations

from typing import Any


SIGNAL_PATCHES = {
    "logs": {
        "gap": "the expected root service did not emit searchable error logs in the evidence window",
        "patch": "add structured error logs with service, operation, status, and upstream request context",
    },
    "traces": {
        "gap": "the expected root service did not have trace evidence strong enough to corroborate the metric anomaly",
        "patch": "record exceptions and error status on the service span, including downstream call spans where applicable",
    },
    "metrics": {
        "gap": "the expected root service did not expose a metric anomaly in the collected telemetry",
        "patch": "add or verify service-level error counters with root-service labels",
    },
}
SERVICE_PATCH_TARGETS = {
    "payment": {
        "logs": ["src/payment/index.js", "src/payment/charge.js", "src/payment/logger.js"],
        "traces": ["src/payment/index.js", "src/payment/charge.js"],
        "metrics": ["src/payment/charge.js"],
    },
    "cart": {
        "logs": ["src/cart"],
        "traces": ["src/cart"],
        "metrics": ["src/cart"],
    },
    "checkout": {
        "logs": ["src/checkout/main.go"],
        "traces": ["src/checkout/main.go"],
        "metrics": ["src/checkout/main.go"],
    },
}


def _patch_for_signal(signal: str) -> dict[str, str]:
    return SIGNAL_PATCHES.get(
        signal,
        {
            "gap": f"the expected root service is missing {signal} evidence",
            "patch": f"add {signal} telemetry for the expected root service",
        },
    )


def _target_files(service: str, signal: str) -> list[str]:
    return SERVICE_PATCH_TARGETS.get(service, {}).get(signal, [f"src/{service}"])


def _validation_query(service: str, signal: str) -> str:
    if signal == "logs":
        return f"python3 scripts/telemetry.py search-logs --text {service} --size 10"
    if signal == "traces":
        return (
            "python3 scripts/telemetry.py query-metrics "
            f"'sum by (service_name, span_name, status_code) "
            f"(traces_span_metrics_calls_total{{service_name=\"{service}\",status_code=\"STATUS_CODE_ERROR\"}})'"
        )
    if signal == "metrics":
        return (
            "python3 scripts/telemetry.py query-metrics "
            f"'sum by (service_name) (traces_span_metrics_calls_total{{service_name=\"{service}\",status_code=\"STATUS_CODE_ERROR\"}})'"
        )
    return "python3 scripts/analyze_eval.py results/eval-runs/<timestamp>"


def detect_blind_spots(analysis: dict[str, Any]) -> list[dict[str, Any]]:
    blind_spots = []
    for miss in analysis.get("misses", []):
        expected = miss.get("expected_root_service")
        if not expected:
            continue
        missing_signals = miss.get("expected_missing_signal_types", [])
        if not miss.get("expected_seen"):
            blind_spots.append(
                {
                    "case_id": miss.get("case_id"),
                    "service": expected,
                    "severity": "high",
                    "missing_signal_types": missing_signals,
                    "gap": "the expected root service did not appear in generated hypotheses",
                    "recommended_patch": "expand telemetry collection so this service appears in metrics, traces, or logs during the incident",
                    "candidate_patch_targets": [f"src/{expected}"],
                    "validation": f"rerun the case and confirm {expected} appears in hypotheses before scoring correctness",
                }
            )
            continue
        expected_signals = set(miss.get("expected_signal_types", []))
        predicted = miss.get("predicted_root_service")
        if predicted and predicted != expected and len(expected_signals & {"metrics", "traces", "logs"}) >= 2:
            blind_spots.append(
                {
                    "case_id": miss.get("case_id"),
                    "service": expected,
                    "severity": "medium",
                    "gap": "the expected root service had corroborating evidence but lost the ranking to a symptom service",
                    "recommended_patch": "add causal scoring that favors downstream root evidence over upstream symptom volume when both candidates are verified",
                    "candidate_patch_targets": ["faultline/agent.py"],
                    "validation": f"rerun the case and confirm {expected} outranks {predicted} when both have verified evidence",
                    "expected_score": miss.get("expected_score"),
                    "predicted_service": predicted,
                    "predicted_score": miss.get("predicted_score"),
                }
            )
        for signal in missing_signals:
            patch = _patch_for_signal(signal)
            blind_spots.append(
                {
                    "case_id": miss.get("case_id"),
                    "service": expected,
                    "severity": "medium",
                    "missing_signal_type": signal,
                    "gap": patch["gap"],
                    "recommended_patch": patch["patch"],
                    "candidate_patch_targets": _target_files(expected, signal),
                    "validation_query": _validation_query(expected, signal),
                    "validation": f"rerun the case and confirm {expected} has {signal} evidence in the diagnosis",
                }
            )
    return blind_spots
