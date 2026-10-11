"""Build instrumentation patch plans from Faultline blind spots."""

from __future__ import annotations

from typing import Any


PATCH_SKETCHES = {
    "logs": {
        "objective": "Make service failures searchable in OpenSearch.",
        "steps": [
            "log failures at error or warn level on the expected root service",
            "include operation, status, error type, and upstream request context",
            "preserve scrubber safety by avoiding injected flag names and sensitive payment fields",
        ],
    },
    "traces": {
        "objective": "Make root-service failures visible as trace evidence.",
        "steps": [
            "record exceptions on the active service span",
            "set span status to error with a stable error type",
            "ensure downstream client spans keep the called service name in the span name",
        ],
    },
    "metrics": {
        "objective": "Make root-service failures measurable in Prometheus.",
        "steps": [
            "emit a service-level error counter with service and operation labels",
            "increment the counter only on failed operations",
            "verify the metric can be queried during the case window",
        ],
    },
}


def _ranking_plan(blind_spot: dict[str, Any]) -> dict[str, Any]:
    service = blind_spot.get("service")
    predicted = blind_spot.get("predicted_service")
    return {
        "case_id": blind_spot.get("case_id"),
        "service": service,
        "kind": "agent_ranking",
        "priority": blind_spot.get("severity", "medium"),
        "objective": "Prefer verified downstream root-cause evidence over verified upstream symptom volume.",
        "target_files": blind_spot.get("candidate_patch_targets", ["faultline/agent.py"]),
        "steps": [
            "keep raw symptom evidence visible in hypotheses",
            "add a causal ranking feature for internal service-to-downstream failures",
            "penalize generic edge or HTTP method spans when they only describe symptoms",
        ],
        "validation": blind_spot.get(
            "validation",
            f"rerun the case and confirm {service} outranks {predicted} when both have verified evidence",
        ),
        "source_gap": blind_spot.get("gap"),
    }


def _telemetry_plan(blind_spot: dict[str, Any]) -> dict[str, Any]:
    signal = blind_spot.get("missing_signal_type", "telemetry")
    sketch = PATCH_SKETCHES.get(
        signal,
        {
            "objective": f"Make {signal} evidence visible for the root service.",
            "steps": [f"add {signal} instrumentation to the expected root service"],
        },
    )
    return {
        "case_id": blind_spot.get("case_id"),
        "service": blind_spot.get("service"),
        "kind": f"instrumentation_{signal}",
        "priority": blind_spot.get("severity", "medium"),
        "objective": sketch["objective"],
        "target_files": blind_spot.get("candidate_patch_targets", []),
        "steps": sketch["steps"],
        "validation": blind_spot.get("validation"),
        "validation_query": blind_spot.get("validation_query"),
        "source_gap": blind_spot.get("gap"),
    }


def build_patch_plan(analysis: dict[str, Any]) -> dict[str, Any]:
    plans = []
    for blind_spot in analysis.get("blind_spots", []):
        if "missing_signal_type" in blind_spot:
            plans.append(_telemetry_plan(blind_spot))
        elif blind_spot.get("candidate_patch_targets") == ["faultline/agent.py"]:
            plans.append(_ranking_plan(blind_spot))
        else:
            plans.append(
                {
                    "case_id": blind_spot.get("case_id"),
                    "service": blind_spot.get("service"),
                    "kind": "telemetry_visibility",
                    "priority": blind_spot.get("severity", "medium"),
                    "objective": blind_spot.get("recommended_patch"),
                    "target_files": blind_spot.get("candidate_patch_targets", []),
                    "steps": [blind_spot.get("recommended_patch", "expand telemetry collection")],
                    "validation": blind_spot.get("validation"),
                    "source_gap": blind_spot.get("gap"),
                }
            )
    return {
        "run_dir": analysis.get("run_dir"),
        "plans": plans,
    }
