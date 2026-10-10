#!/usr/bin/env python3
"""Analyze a Faultline evaluation run and explain missed diagnoses."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from faultline.analysis import analyze_run


def main() -> int:
    parser = argparse.ArgumentParser(description="Analyze missed diagnoses in an evaluation run.")
    parser.add_argument("run_dir", type=Path)
    parser.add_argument("--cases", type=Path, default=Path("cases/day2_feature_flags.json"))
    args = parser.parse_args()

    print(json.dumps(analyze_run(args.run_dir, args.cases), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
