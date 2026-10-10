#!/usr/bin/env python3
"""Run and snapshot Faultline incident cases against the OpenTelemetry Demo."""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_CASES = Path("cases/day2_feature_flags.json")
DEFAULT_FLAG_API = "http://localhost:8080/feature/api"
DEFAULT_PROMETHEUS = "http://localhost:9090"
DEFAULT_OPENSEARCH = "http://localhost:56846"
DEFAULT_JAEGER_UI = "http://localhost:56848/jaeger/ui/"
DEFAULT_SNAPSHOT_DIR = Path("snapshots")
DEFAULT_CHANGE_LOG = Path("runs/change-log.jsonl")
FAULT_FLAGS = {"adFailure", "cartFailure", "paymentFailure"}
PROMETHEUS_QUERIES = {
    "span_calls": "traces_span_metrics_calls_total",
    "span_errors": "traces_span_metrics_calls_total{status_code=\"STATUS_CODE_ERROR\"}",
    "ad_requests": "demo_ad_requests_total",
    "cart_latency": "demo_cart_get_cart_latency_seconds_count",
    "payment_spans": "traces_span_metrics_calls_total{service_name=\"payment\"}",
    "frontend_errors": "traces_span_metrics_calls_total{service_name=\"frontend\",status_code=\"STATUS_CODE_ERROR\"}"
}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def request_json(method: str, url: str, payload: dict | None = None) -> dict:
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
        raise SystemExit(f"Request failed for {url}: {exc}") from exc
    return json.loads(body) if body else {}


def request_text(url: str) -> str:
    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            return response.read().decode("utf-8", errors="replace")
    except urllib.error.URLError as exc:
        return f"unavailable: {exc}"


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def load_case_file(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def cases_by_id(case_file: dict) -> dict[str, dict]:
    return {case["case_id"]: case for case in case_file["cases"]}


def read_flags(api: str) -> dict:
    return request_json("GET", f"{api}/read")


def write_flags(api: str, config: dict) -> None:
    request_json("POST", f"{api}/write", {"data": config})


def validate_case(case: dict, live_flags: dict) -> list[str]:
    errors = []
    fault = case.get("fault", {})
    if fault.get("type") != "flag":
        errors.append(f"{case.get('case_id')}: unsupported fault type {fault.get('type')!r}")
        return errors
    flag = fault.get("name")
    variant = fault.get("variant")
    flags = live_flags.get("flags", {})
    if flag not in flags:
        errors.append(f"{case.get('case_id')}: flag {flag!r} does not exist in live demo")
    elif variant not in flags[flag].get("variants", {}):
        variants = ", ".join(flags[flag].get("variants", {}))
        errors.append(f"{case.get('case_id')}: variant {variant!r} not available for {flag}; live variants: {variants}")
    return errors


def validate_cases(case_file: dict, api: str) -> None:
    live_flags = read_flags(api)
    errors = []
    seen = set()
    for case in case_file["cases"]:
        case_id = case.get("case_id")
        if case_id in seen:
            errors.append(f"duplicate case_id: {case_id}")
        seen.add(case_id)
        errors.extend(validate_case(case, live_flags))
    if errors:
        raise SystemExit("Case validation failed:\n- " + "\n- ".join(errors))


def reset_fault_flags(api: str) -> None:
    config = read_flags(api)
    for flag in FAULT_FLAGS:
        if flag in config.get("flags", {}) and "off" in config["flags"][flag].get("variants", {}):
            config["flags"][flag]["defaultVariant"] = "off"
    write_flags(api, config)


def apply_case(case: dict, api: str, change_log: Path) -> None:
    reset_fault_flags(api)
    config = read_flags(api)
    fault = case["fault"]
    flag = fault["name"]
    variant = fault["variant"]
    errors = validate_case(case, config)
    if errors:
        raise SystemExit("Cannot apply case:\n- " + "\n- ".join(errors))
    config["flags"][flag]["defaultVariant"] = variant
    write_flags(api, config)
    if "decoy_change" in case:
        record = {
            "recorded_at": now_iso(),
            "case_id": case["case_id"],
            "change": case["decoy_change"],
            "note": "Simulated decoy change for future recent_changes tool."
        }
        change_log.parent.mkdir(parents=True, exist_ok=True)
        with change_log.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, sort_keys=True) + "\n")


def prometheus_query(base_url: str, query: str) -> dict:
    params = urllib.parse.urlencode({"query": query})
    return request_json("GET", f"{base_url}/api/v1/query?{params}")


def opensearch_logs(base_url: str, size: int) -> dict:
    payload = {
        "size": size,
        "sort": [{"@timestamp": {"order": "desc"}}],
        "query": {"match_all": {}}
    }
    return request_json("POST", f"{base_url}/otel-logs-*/_search", payload)


def snapshot_case(
    case: dict,
    snapshot_dir: Path,
    flag_api: str,
    prometheus_url: str,
    opensearch_url: str,
    jaeger_ui_url: str,
    log_limit: int,
) -> Path:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_dir = snapshot_dir / case["case_id"] / stamp
    out_dir.mkdir(parents=True, exist_ok=True)

    metadata = {
        "case_id": case["case_id"],
        "captured_at": now_iso(),
        "telemetry_sources": {
            "flags": flag_api,
            "prometheus": prometheus_url,
            "opensearch": opensearch_url,
            "jaeger_ui": jaeger_ui_url
        }
    }
    write_json(out_dir / "metadata.json", metadata)
    write_json(out_dir / "case.json", case)
    write_json(out_dir / "flags.json", read_flags(flag_api))
    write_json(out_dir / "prometheus.json", {name: prometheus_query(prometheus_url, query) for name, query in PROMETHEUS_QUERIES.items()})
    write_json(out_dir / "opensearch_logs.json", opensearch_logs(opensearch_url, log_limit))
    (out_dir / "jaeger_ui_check.txt").write_text(request_text(jaeger_ui_url)[:500], encoding="utf-8")
    return out_dir


def print_cases(case_file: dict) -> None:
    for case in case_file["cases"]:
        fault = case["fault"]
        decoy = " decoy" if "decoy_change" in case else ""
        print(f"{case['case_id']}: {fault['name']}={fault['variant']} split={case['split']} role={case['loop_role']}{decoy}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate, apply, reset, and snapshot Faultline cases.")
    parser.add_argument("--cases", type=Path, default=DEFAULT_CASES)
    parser.add_argument("--flag-api", default=DEFAULT_FLAG_API)
    parser.add_argument("--prometheus", default=DEFAULT_PROMETHEUS)
    parser.add_argument("--opensearch", default=DEFAULT_OPENSEARCH)
    parser.add_argument("--jaeger-ui", default=DEFAULT_JAEGER_UI)
    parser.add_argument("--snapshot-dir", type=Path, default=DEFAULT_SNAPSHOT_DIR)
    parser.add_argument("--change-log", type=Path, default=DEFAULT_CHANGE_LOG)
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("list")
    subparsers.add_parser("validate")

    apply_parser = subparsers.add_parser("apply")
    apply_parser.add_argument("case_id")

    subparsers.add_parser("reset")

    snapshot_parser = subparsers.add_parser("snapshot")
    snapshot_parser.add_argument("case_id")
    snapshot_parser.add_argument("--log-limit", type=int, default=50)

    run_parser = subparsers.add_parser("run")
    run_parser.add_argument("case_id")
    run_parser.add_argument("--hold-seconds", type=float, default=30.0)
    run_parser.add_argument("--log-limit", type=int, default=50)

    args = parser.parse_args()
    case_file = load_case_file(args.cases)
    case_map = cases_by_id(case_file)

    if args.command == "list":
        print_cases(case_file)
    elif args.command == "validate":
        validate_cases(case_file, args.flag_api)
        print(f"Validated {len(case_file['cases'])} cases against live flags")
    elif args.command == "apply":
        apply_case(case_map[args.case_id], args.flag_api, args.change_log)
        fault = case_map[args.case_id]["fault"]
        print(f"Applied {args.case_id}: {fault['name']}={fault['variant']}")
    elif args.command == "reset":
        reset_fault_flags(args.flag_api)
        print("Reset Day 2 fault flags to off")
    elif args.command == "snapshot":
        out_dir = snapshot_case(case_map[args.case_id], args.snapshot_dir, args.flag_api, args.prometheus, args.opensearch, args.jaeger_ui, args.log_limit)
        print(f"Wrote snapshot to {out_dir}")
    elif args.command == "run":
        case = case_map[args.case_id]
        apply_case(case, args.flag_api, args.change_log)
        print(f"Applied {args.case_id}; waiting {args.hold_seconds:g}s for telemetry")
        time.sleep(args.hold_seconds)
        out_dir = snapshot_case(case, args.snapshot_dir, args.flag_api, args.prometheus, args.opensearch, args.jaeger_ui, args.log_limit)
        reset_fault_flags(args.flag_api)
        print(f"Wrote snapshot to {out_dir}")
        print("Reset Day 2 fault flags to off")
    return 0


if __name__ == "__main__":
    sys.exit(main())
