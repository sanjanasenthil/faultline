#!/usr/bin/env python3
"""Score Faultline diagnosis JSON files against known cases."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from faultline.eval import load_cases, score_diagnosis, summarize_scores


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate diagnosis outputs against case ground truth.")
    parser.add_argument("--cases", type=Path, default=Path("cases/day2_feature_flags.json"))
    parser.add_argument("diagnosis_files", nargs="+", type=Path)
    args = parser.parse_args()

    cases = load_cases(args.cases)
    scores = []
    for diagnosis_file in args.diagnosis_files:
        diagnosis = json.loads(diagnosis_file.read_text(encoding="utf-8"))
        case_id = diagnosis.get("case_id") or diagnosis_file.stem
        if case_id not in cases:
            raise SystemExit(f"No case named {case_id!r} in {args.cases}")
        scores.append(score_diagnosis(cases[case_id], diagnosis))
    print(json.dumps(summarize_scores(scores), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
