#!/usr/bin/env python3
"""Write a patch-plan bundle from a Faultline evaluation run."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from faultline.analysis import analyze_run
from faultline.artifacts import write_patch_bundle


def main() -> int:
    parser = argparse.ArgumentParser(description="Write a patch bundle for a saved evaluation run.")
    parser.add_argument("run_dir", type=Path)
    parser.add_argument("--cases", type=Path, default=Path("cases/day2_feature_flags.json"))
    parser.add_argument("--output-dir", type=Path)
    args = parser.parse_args()

    analysis = analyze_run(args.run_dir, args.cases)
    paths = write_patch_bundle(analysis, args.output_dir)
    for name, path in paths.items():
        print(f"{name}: {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
