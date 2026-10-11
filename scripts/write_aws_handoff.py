#!/usr/bin/env python3
"""Write AWS handoff files for a Faultline evaluation run."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from faultline.aws import write_aws_handoff


def main() -> int:
    parser = argparse.ArgumentParser(description="Write AWS handoff files for a saved evaluation run.")
    parser.add_argument("run_dir", type=Path)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--patch-bundle-dir", type=Path)
    args = parser.parse_args()

    paths = write_aws_handoff(args.run_dir, args.output_dir, args.patch_bundle_dir)
    for name, path in paths.items():
        print(f"{name}: {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
