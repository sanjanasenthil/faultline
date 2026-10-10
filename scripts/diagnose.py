#!/usr/bin/env python3
"""Run the Faultline diagnosis agent."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from faultline import agent, telemetry


def print_json(payload: object) -> None:
    print(json.dumps(payload, indent=2, sort_keys=True))


def main() -> int:
    parser = argparse.ArgumentParser(description="Diagnose an incident from live telemetry or a saved snapshot.")
    parser.add_argument("--prometheus", default=telemetry.DEFAULT_PROMETHEUS)
    parser.add_argument("--opensearch", default=telemetry.DEFAULT_OPENSEARCH)
    parser.add_argument("--jaeger-ui", default=telemetry.DEFAULT_JAEGER_UI)
    parser.add_argument("--change-log", type=Path, default=telemetry.DEFAULT_CHANGE_LOG)
    subparsers = parser.add_subparsers(dest="command", required=True)

    live_parser = subparsers.add_parser("live")
    live_parser.add_argument("--alert-service", default="frontend")
    live_parser.add_argument("--symptom", default="unknown")

    snapshot_parser = subparsers.add_parser("snapshot")
    snapshot_parser.add_argument("snapshot_dir", type=Path)

    args = parser.parse_args()

    if args.command == "live":
        bundle = agent.collect_live_bundle(
            alert_service=args.alert_service,
            symptom=args.symptom,
            prometheus_url=args.prometheus,
            opensearch_url=args.opensearch,
            jaeger_ui_url=args.jaeger_ui,
            change_log=args.change_log,
        )
    elif args.command == "snapshot":
        bundle = agent.load_snapshot_bundle(args.snapshot_dir)
    else:
        parser.error("unknown command")

    print_json(agent.diagnose(bundle))
    return 0


if __name__ == "__main__":
    sys.exit(main())
