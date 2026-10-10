"""Scrub telemetry so injected fault labels cannot leak to the diagnosis agent."""

from __future__ import annotations

import copy
import re
from typing import Any


FLAG_NAMES = {
    "adFailure",
    "adHighCpu",
    "adManualGc",
    "cartFailure",
    "emailMemoryLeak",
    "failedReadinessProbe",
    "imageSlowLoad",
    "intlShippingSlowdown",
    "kafkaConsumerDead",
    "kafkaQueueProblems",
    "loadGeneratorFloodHomepage",
    "paymentFailure",
    "paymentUnreachable",
    "productCatalogFailure",
    "productCatalogLockContention",
    "recommendationCacheFailure",
}

INJECTOR_TERMS = {
    "flagd",
    "flagservice",
    "openfeature",
    "feature_flag",
    "feature-flag",
    "feature flag",
    "faultline.injector",
    "injected_fault",
    "fault_variant",
}

FAULT_HINT_TERMS = {
    "adFailure",
    "cartFailure",
    "paymentFailure",
    "paymentUnreachable",
    "productCatalogFailure",
    "productCatalogLockContention",
    "recommendationCacheFailure",
    "kafkaQueueProblems",
}

REDACTION = "[REDACTED]"


def forbidden_terms() -> set[str]:
    return set(FLAG_NAMES) | set(INJECTOR_TERMS) | set(FAULT_HINT_TERMS)


def contains_forbidden_term(value: Any) -> bool:
    text = str(value).lower()
    return any(term.lower() in text for term in forbidden_terms())


def is_flag_related_key(key: str) -> bool:
    normalized = key.lower().replace("-", "_")
    return (
        "flag" in normalized
        or "openfeature" in normalized
        or normalized in {"variant", "reason"}
        or contains_forbidden_term(key)
    )


def is_flagd_record(record: dict[str, Any]) -> bool:
    searchable = []
    for path in (
        ("service.name",),
        ("service_name",),
        ("job",),
        ("resource", "service.name"),
        ("attributes", "service.name"),
        ("metric", "service_name"),
        ("metric", "job"),
        ("span_name",),
        ("name",),
    ):
        current: Any = record
        for part in path:
            if not isinstance(current, dict) or part not in current:
                current = None
                break
            current = current[part]
        if current is not None:
            searchable.append(str(current))
    return any("flagd" in value.lower() or "openfeature" in value.lower() for value in searchable)


def redact_string(value: str) -> str:
    redacted = value
    for term in sorted(forbidden_terms(), key=len, reverse=True):
        redacted = re.sub(re.escape(term), REDACTION, redacted, flags=re.IGNORECASE)
    return redacted


def scrub(value: Any) -> Any:
    """Return a scrubbed copy of a telemetry payload.

    The scrubber removes flagd/OpenFeature records entirely and redacts flag names
    or injector labels from surviving fields.
    """

    return _scrub(copy.deepcopy(value))


def _scrub(value: Any) -> Any:
    if isinstance(value, dict):
        if is_flagd_record(value):
            return None
        result = {}
        for key, child in value.items():
            if is_flag_related_key(str(key)):
                continue
            scrubbed = _scrub(child)
            if scrubbed is not None:
                result[key] = scrubbed
        if "metric" in value and not result.get("metric"):
            return None
        return result
    if isinstance(value, list):
        result = []
        for item in value:
            scrubbed = _scrub(item)
            if scrubbed is not None:
                result.append(scrubbed)
        return result
    if isinstance(value, str):
        return redact_string(value)
    return value


def assert_no_leakage(payload: Any) -> None:
    serialized = str(payload).lower()
    leaked = sorted(term for term in forbidden_terms() if term.lower() in serialized)
    if leaked:
        raise AssertionError(f"scrubbed payload leaked forbidden terms: {', '.join(leaked)}")
