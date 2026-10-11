#!/usr/bin/env python3
"""Write a markdown patch-plan artifact from a Faultline evaluation run."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from faultline.analysis import analyze_run
from faultline.artifacts import write_patch_plan_artifact


def main() -> int:
    parser = argparse.ArgumentParser(description="Write patch-plan.md for a saved evaluation run.")
    parser.add_argument("run_dir", type=Path)
    parser.add_argument("--cases", type=Path, default=Path("cases/day2_feature_flags.json"))
    parser.add_argument("--output-dir", type=Path)
    args = parser.parse_args()

    analysis = analyze_run(args.run_dir, args.cases)
    path = write_patch_plan_artifact(analysis, args.output_dir)
    print(path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
