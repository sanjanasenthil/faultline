"""Evidence verification for Faultline diagnoses."""

from __future__ import annotations

from typing import Any


INDEPENDENT_SIGNAL_TYPES = {"metrics", "traces", "logs"}
DECOY_SIGNAL_TYPES = {"changes"}


def non_change_signals(evidence: dict[str, Any]) -> list[str]:
    return [signal for signal in evidence.get("signal_types", []) if signal not in DECOY_SIGNAL_TYPES]


def verify_evidence(evidence: dict[str, Any], min_signal_types: int = 2) -> dict[str, Any]:
    """Verify whether a candidate has enough independent evidence.

    Recent changes are intentionally excluded because Day 2 can generate decoy
    deploy records. They remain useful context, but not proof.
    """

    service = evidence.get("service")
    signals = non_change_signals(evidence)
    missing = sorted(INDEPENDENT_SIGNAL_TYPES - set(signals))
    verified = bool(service) and len(signals) >= min_signal_types
    if verified:
        reason = f"{service} has {len(signals)} independent telemetry signal types: {', '.join(signals)}"
    elif service:
        reason = f"{service} has only {len(signals)} independent telemetry signal type(s); need {min_signal_types}"
    else:
        reason = "no candidate service was provided"
    return {
        "verified": verified,
        "service": service,
        "independent_signal_types": signals,
        "missing_signal_types": missing,
        "min_signal_types": min_signal_types,
        "reason": reason,
    }


def verify_hypotheses(hypotheses: list[dict[str, Any]], min_signal_types: int = 2) -> list[dict[str, Any]]:
    return [verify_evidence(hypothesis, min_signal_types) for hypothesis in hypotheses]
