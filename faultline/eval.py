"""Evaluation helpers for Faultline diagnoses."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_cases(path: Path) -> dict[str, dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return {case["case_id"]: case for case in data["cases"]}


def score_diagnosis(case: dict[str, Any], diagnosis: dict[str, Any]) -> dict[str, Any]:
    expected = case.get("ground_truth", {}).get("root_service")
    predicted = diagnosis.get("conclusion", {}).get("root_service")
    verification = diagnosis.get("conclusion", {}).get("verification", {})
    confidence = diagnosis.get("conclusion", {}).get("confidence")
    abstained = confidence == "abstain" or predicted is None
    correct = bool(predicted and expected and predicted == expected)
    return {
        "case_id": case.get("case_id"),
        "expected_root_service": expected,
        "predicted_root_service": predicted,
        "confidence": confidence,
        "verified": bool(verification.get("verified")),
        "abstained": abstained,
        "correct": correct,
    }


def summarize_scores(scores: list[dict[str, Any]]) -> dict[str, Any]:
    attempted = [score for score in scores if not score["abstained"]]
    correct = [score for score in attempted if score["correct"]]
    verified = [score for score in scores if score["verified"]]
    return {
        "cases": len(scores),
        "attempted": len(attempted),
        "abstained": len(scores) - len(attempted),
        "correct": len(correct),
        "accuracy_on_attempted": round(len(correct) / len(attempted), 3) if attempted else None,
        "verified_conclusions": len(verified),
        "scores": scores,
    }
