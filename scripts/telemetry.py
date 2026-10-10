#!/usr/bin/env python3
"""CLI wrapper for Faultline telemetry tools."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from faultline import telemetry
from faultline.scrubber import assert_no_leakage


def print_json(payload: object) -> None:
    print(json.dumps(payload, indent=2, sort_keys=True))


def main() -> int:
    parser = argparse.ArgumentParser(description="Query scrubbed Faultline telemetry.")
    parser.add_argument("--prometheus", default=telemetry.DEFAULT_PROMETHEUS)
    parser.add_argument("--opensearch", default=telemetry.DEFAULT_OPENSEARCH)
    parser.add_argument("--jaeger-ui", default=telemetry.DEFAULT_JAEGER_UI)
    parser.add_argument("--change-log", type=Path, default=telemetry.DEFAULT_CHANGE_LOG)
    parser.add_argument("--raw", action="store_true", help="Return raw, unscrubbed data. For local debugging only.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    metrics_parser = subparsers.add_parser("query-metrics")
    metrics_parser.add_argument("query")

    logs_parser = subparsers.add_parser("search-logs")
    logs_parser.add_argument("--text")
    logs_parser.add_argument("--size", type=int, default=20)

    subparsers.add_parser("list-anomalies")
    subparsers.add_parser("get-trace")
    subparsers.add_parser("service-dependencies")

    changes_parser = subparsers.add_parser("recent-changes")
    changes_parser.add_argument("--limit", type=int, default=20)

    runbooks_parser = subparsers.add_parser("search-runbooks")
    runbooks_parser.add_argument("query")

    args = parser.parse_args()
    should_scrub = not args.raw

    if args.command == "query-metrics":
        payload = telemetry.query_metrics(args.query, args.prometheus, should_scrub)
    elif args.command == "search-logs":
        payload = telemetry.search_logs(args.text, args.size, args.opensearch, should_scrub)
    elif args.command == "list-anomalies":
        payload = telemetry.list_anomalies(args.prometheus, should_scrub)
    elif args.command == "get-trace":
        payload = telemetry.get_trace_summary(args.prometheus, args.jaeger_ui, should_scrub)
    elif args.command == "service-dependencies":
        payload = telemetry.service_dependencies(args.prometheus, should_scrub)
    elif args.command == "recent-changes":
        payload = telemetry.recent_changes(args.change_log, args.limit, should_scrub)
    elif args.command == "search-runbooks":
        payload = telemetry.search_runbooks(args.query)
    else:
        parser.error("unknown command")

    if should_scrub:
        assert_no_leakage(payload)
    print_json(payload)
    return 0


if __name__ == "__main__":
    sys.exit(main())
