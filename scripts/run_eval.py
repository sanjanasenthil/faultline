#!/usr/bin/env python3
"""Run Faultline cases end-to-end and score diagnoses."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from faultline import harness, telemetry

import importlib.util


CASES_SCRIPT = ROOT / "scripts" / "cases.py"
spec = importlib.util.spec_from_file_location("faultline_cases_script", CASES_SCRIPT)
if spec is None or spec.loader is None:
    raise RuntimeError(f"could not load {CASES_SCRIPT}")
cases_script = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cases_script)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run and score Faultline diagnosis cases.")
    parser.add_argument("--cases", type=Path, default=Path("cases/day2_feature_flags.json"))
    parser.add_argument("--case-id", action="append", dest="case_ids", help="Run one case id. Repeat to run multiple.")
    parser.add_argument("--limit", type=int, help="Run the first N selected cases.")
    parser.add_argument("--hold-seconds", type=float, default=30.0)
    parser.add_argument("--flag-api", default="http://localhost:8080/feature/api")
    parser.add_argument("--prometheus", default=telemetry.DEFAULT_PROMETHEUS)
    parser.add_argument("--opensearch", default=telemetry.DEFAULT_OPENSEARCH)
    parser.add_argument("--jaeger-ui", default=telemetry.DEFAULT_JAEGER_UI)
    parser.add_argument("--change-log", type=Path, default=telemetry.DEFAULT_CHANGE_LOG)
    parser.add_argument("--output-dir", type=Path, default=Path("results/eval-runs"))
    args = parser.parse_args()

    case_file = harness.load_case_file(args.cases)
    selected = harness.select_cases(case_file, args.case_ids, args.limit)
    if not selected:
        raise SystemExit("no cases selected")

    summary = harness.run_evaluation(
        selected,
        apply_case_fn=cases_script.apply_case,
        reset_fn=cases_script.reset_fault_flags,
        flag_api=args.flag_api,
        change_log=args.change_log,
        hold_seconds=args.hold_seconds,
        prometheus_url=args.prometheus,
        opensearch_url=args.opensearch,
        jaeger_ui_url=args.jaeger_ui,
        output_dir=args.output_dir,
    )
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
