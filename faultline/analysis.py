"""Analyze Faultline evaluation runs for diagnosis gaps."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .blindspots import detect_blind_spots
from .eval import load_cases
from .verifier import INDEPENDENT_SIGNAL_TYPES


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _find_hypothesis(diagnosis: dict[str, Any], service: str | None) -> dict[str, Any] | None:
    if not service:
        return None
    for hypothesis in diagnosis.get("hypotheses", []):
        if hypothesis.get("service") == service:
            return hypothesis
    return None


def _missing_signals(hypothesis: dict[str, Any] | None) -> list[str]:
    if not hypothesis:
        return sorted(INDEPENDENT_SIGNAL_TYPES)
    present = set(hypothesis.get("signal_types", []))
    return sorted(INDEPENDENT_SIGNAL_TYPES - present)


def analyze_run(run_dir: Path, cases_path: Path) -> dict[str, Any]:
    cases = load_cases(cases_path)
    summary = load_json(run_dir / "summary.json")
    diagnoses_dir = run_dir / "diagnoses"
    misses = []

    for score in summary.get("scores", []):
        if score.get("correct"):
            continue
        case_id = score.get("case_id")
        case = cases.get(case_id, {})
        diagnosis_path = diagnoses_dir / f"{case_id}.json"
        diagnosis = load_json(diagnosis_path) if diagnosis_path.exists() else {}
        expected = score.get("expected_root_service")
        predicted = score.get("predicted_root_service")
        expected_hypothesis = _find_hypothesis(diagnosis, expected)
        predicted_hypothesis = _find_hypothesis(diagnosis, predicted)
        misses.append(
            {
                "case_id": case_id,
                "alert": case.get("alert", {}),
                "expected_root_service": expected,
                "predicted_root_service": predicted,
                "predicted_verified": score.get("verified"),
                "expected_seen": expected_hypothesis is not None,
                "expected_score": expected_hypothesis.get("score") if expected_hypothesis else None,
                "expected_signal_types": expected_hypothesis.get("signal_types", []) if expected_hypothesis else [],
                "expected_missing_signal_types": _missing_signals(expected_hypothesis),
                "predicted_score": predicted_hypothesis.get("score") if predicted_hypothesis else None,
                "predicted_signal_types": predicted_hypothesis.get("signal_types", []) if predicted_hypothesis else [],
                "diagnosis_path": str(diagnosis_path),
            }
        )

    report = {
        "run_dir": str(run_dir),
        "cases": summary.get("cases", 0),
        "correct": summary.get("correct", 0),
        "attempted": summary.get("attempted", 0),
        "accuracy_on_attempted": summary.get("accuracy_on_attempted"),
        "misses": misses,
    }
    report["blind_spots"] = detect_blind_spots(report)
    return report
