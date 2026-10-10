"""End-to-end evaluation harness for Faultline cases."""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from . import agent
from .eval import score_diagnosis, summarize_scores
from .scrubber import assert_no_leakage


def now_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def load_case_file(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def select_cases(case_file: dict[str, Any], case_ids: list[str] | None = None, limit: int | None = None) -> list[dict[str, Any]]:
    cases = case_file["cases"]
    if case_ids:
        wanted = set(case_ids)
        cases = [case for case in cases if case["case_id"] in wanted]
        missing = wanted - {case["case_id"] for case in cases}
        if missing:
            raise ValueError(f"unknown case id(s): {', '.join(sorted(missing))}")
    if limit is not None:
        cases = cases[:limit]
    return cases


def evaluate_case(
    case: dict[str, Any],
    *,
    apply_case_fn,
    reset_fn,
    flag_api: str,
    change_log: Path,
    hold_seconds: float,
    prometheus_url: str,
    opensearch_url: str,
    jaeger_ui_url: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    try:
        apply_case_fn(case, flag_api, change_log)
        time.sleep(hold_seconds)
        bundle = agent.collect_live_bundle(
            alert_service=case.get("alert", {}).get("service", "frontend"),
            symptom=case.get("alert", {}).get("symptom", "unknown"),
            prometheus_url=prometheus_url,
            opensearch_url=opensearch_url,
            jaeger_ui_url=jaeger_ui_url,
            change_log=change_log,
        )
        diagnosis = agent.diagnose(bundle)
        diagnosis["case_id"] = case["case_id"]
        assert_no_leakage(diagnosis)
        score = score_diagnosis(case, diagnosis)
        return diagnosis, score
    finally:
        reset_fn(flag_api)


def run_evaluation(
    cases: list[dict[str, Any]],
    *,
    apply_case_fn,
    reset_fn,
    flag_api: str,
    change_log: Path,
    hold_seconds: float,
    prometheus_url: str,
    opensearch_url: str,
    jaeger_ui_url: str,
    output_dir: Path,
) -> dict[str, Any]:
    run_dir = output_dir / now_stamp()
    diagnoses_dir = run_dir / "diagnoses"
    scores = []
    errors = []

    for case in cases:
        try:
            diagnosis, score = evaluate_case(
                case,
                apply_case_fn=apply_case_fn,
                reset_fn=reset_fn,
                flag_api=flag_api,
                change_log=change_log,
                hold_seconds=hold_seconds,
                prometheus_url=prometheus_url,
                opensearch_url=opensearch_url,
                jaeger_ui_url=jaeger_ui_url,
            )
            write_json(diagnoses_dir / f"{case['case_id']}.json", diagnosis)
            scores.append(score)
        except Exception as exc:  # noqa: BLE001 - harness records per-case failures.
            errors.append({"case_id": case["case_id"], "error": str(exc)})
            try:
                reset_fn(flag_api)
            except Exception as reset_exc:  # noqa: BLE001 - preserve reset failure details.
                errors[-1]["reset_error"] = str(reset_exc)

    summary = summarize_scores(scores)
    summary["errors"] = errors
    summary["run_dir"] = str(run_dir)
    summary["hold_seconds"] = hold_seconds
    write_json(run_dir / "summary.json", summary)
    return summary
