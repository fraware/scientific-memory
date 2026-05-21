#!/usr/bin/env python3
"""Validate PCS rendering benchmark output directory (v0 reports + pcs-bench ingest)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "pipeline" / "src"))

from sm_pipeline.benchmark.pcs_core_benchmark_validate import (
    resolve_pcs_core_from_env,
    resolve_pcs_core_root,
)
from sm_pipeline.benchmark.report_builder import normalize_benchmark_out_dir, validate_benchmark_output_dir


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "out_dir",
        nargs="?",
        default="benchmark_runs/pcs_rendering",
        help="Benchmark output directory (default: benchmark_runs/pcs_rendering)",
    )
    parser.add_argument(
        "--out",
        "-o",
        dest="out_dir_flag",
        default="",
        help="Benchmark output directory (preferred over positional)",
    )
    parser.add_argument(
        "--repo-root",
        default=str(REPO_ROOT),
        help="Scientific Memory repo root",
    )
    parser.add_argument(
        "--validate-pcs-core-output",
        nargs="?",
        const="",
        default=None,
        metavar="PCS_CORE_ROOT",
        help=(
            "Also validate against pcs-core schemas. "
            "Flag alone uses PCS_CORE_PATH/PCS_CORE_ROOT; optional path overrides."
        ),
    )
    parser.add_argument(
        "--require-pcs-core",
        action="store_true",
        help="Fail when pcs-core validation was requested but checkout/schemas are unavailable",
    )
    args = parser.parse_args()
    raw = args.out_dir_flag or args.out_dir or "benchmark_runs/pcs_rendering"
    out_dir = Path(normalize_benchmark_out_dir(raw))
    if not out_dir.is_absolute():
        out_dir = REPO_ROOT / out_dir
    repo_root = Path(args.repo_root).resolve()

    pcs_core_root = None
    if args.validate_pcs_core_output is not None:
        raw = str(args.validate_pcs_core_output).strip()
        pcs_core_root = (
            resolve_pcs_core_from_env(repo_root=repo_root)
            if raw == ""
            else resolve_pcs_core_root(raw, repo_root=repo_root)
        )
        if pcs_core_root is None:
            print(
                "pcs-core root not found for validation "
                f"(arg={args.validate_pcs_core_output!r})",
                file=sys.stderr,
            )
            return 1
    elif args.require_pcs_core:
        pcs_core_root = resolve_pcs_core_from_env(repo_root=repo_root)
        if pcs_core_root is None:
            print("pcs-core required but PCS_CORE_PATH/PCS_CORE_ROOT not set", file=sys.stderr)
            return 1
    errors = validate_benchmark_output_dir(out_dir, repo_root, pcs_core_root=pcs_core_root)
    if errors:
        for msg in errors:
            print(msg, file=sys.stderr)
        return 1
    print(f"OK: {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
