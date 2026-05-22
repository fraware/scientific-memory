#!/usr/bin/env python3
"""Validate a standalone pcs_bench_ingest.v0.json (embedded contract + pcs-core schemas)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "pipeline" / "src"))

from sm_pipeline.benchmark.pcs_core_benchmark_validate import resolve_pcs_core_from_env, resolve_pcs_core_root
from sm_pipeline.benchmark.report_builder import validate_pcs_bench_ingest_file


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input",
        "-i",
        required=True,
        help="Path to pcs_bench_ingest.v0.json",
    )
    parser.add_argument(
        "--pcs-core",
        required=True,
        help="pcs-core checkout root for schema validation",
    )
    parser.add_argument(
        "--release-grade",
        action="store_true",
        help="Enforce release-grade producer gates (commit, coverage thresholds)",
    )
    parser.add_argument(
        "--repo-root",
        default=str(REPO_ROOT),
        help="Scientific Memory repo root",
    )
    parser.add_argument(
        "--skip-pcs-bench-cli",
        action="store_true",
        help="Do not invoke external pcs-bench validate-ingest",
    )
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    ingest_path = Path(args.input)
    if not ingest_path.is_absolute():
        ingest_path = repo_root / ingest_path

    pcs_core_root = resolve_pcs_core_root(args.pcs_core, repo_root=repo_root)
    if pcs_core_root is None:
        pcs_core_root = resolve_pcs_core_from_env(repo_root=repo_root)
    if pcs_core_root is None:
        print(f"pcs-core root not found: {args.pcs_core}", file=sys.stderr)
        return 1

    errors = validate_pcs_bench_ingest_file(
        ingest_path,
        repo_root,
        pcs_core_root=pcs_core_root,
        release_grade=args.release_grade,
        invoke_pcs_bench_cli=not args.skip_pcs_bench_cli,
        require_pcs_bench_cli=args.release_grade and not args.skip_pcs_bench_cli,
    )
    if errors:
        for msg in errors:
            print(msg, file=sys.stderr)
        return 1
    print(f"OK: {ingest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
