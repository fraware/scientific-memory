#!/usr/bin/env python3
"""Validate PCS rendering benchmark output directory (v0 reports + pcs-bench ingest)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "pipeline" / "src"))

from sm_pipeline.benchmark.report_builder import validate_benchmark_output_dir


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "out_dir",
        nargs="?",
        default="benchmark_runs/pcs_rendering",
        help="Benchmark output directory (default: benchmark_runs/pcs_rendering)",
    )
    parser.add_argument(
        "--repo-root",
        default=str(REPO_ROOT),
        help="Scientific Memory repo root",
    )
    args = parser.parse_args()
    out_dir = Path(args.out_dir)
    if not out_dir.is_absolute():
        out_dir = REPO_ROOT / out_dir
    repo_root = Path(args.repo_root).resolve()

    errors = validate_benchmark_output_dir(out_dir, repo_root)
    if errors:
        for msg in errors:
            print(msg, file=sys.stderr)
        return 1
    print(f"OK: {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
