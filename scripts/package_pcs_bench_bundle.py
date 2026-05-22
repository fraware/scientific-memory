#!/usr/bin/env python3
"""Copy a validated PCS benchmark output directory into a pcs-bench upload bundle layout."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "pipeline" / "src"))

from sm_pipeline.benchmark.bench_registry import build_run_suite_manifest
from sm_pipeline.benchmark.pcs_core_benchmark_validate import resolve_pcs_core_root
from sm_pipeline.benchmark.report_builder import (
    PCS_BENCH_INGEST_FILENAME,
    validate_benchmark_output_dir,
)

REQUIRED_FILES = (
    PCS_BENCH_INGEST_FILENAME,
    "benchmark_run.v0.json",
    "rendering_coverage_report.v0.json",
    "explain_quality_report.v0.json",
    "query_coverage_report.v0.json",
    "failed_release_rendering_report.v0.json",
    "pcs_bench_payload.json",
    "rendering_benchmark_summary.md",
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "source_dir",
        help="Validated benchmark output (e.g. benchmark_runs/pcs_rendering)",
    )
    parser.add_argument(
        "--dest",
        default=None,
        help="Destination bundle directory (default: <source>_bundle)",
    )
    parser.add_argument(
        "--validate-pcs-core-output",
        nargs="?",
        const="",
        default=None,
        metavar="PCS_CORE_ROOT",
        help="Validate source dir against pcs-core schemas before packaging",
    )
    parser.add_argument(
        "--release-grade",
        action="store_true",
        help="Enforce release-grade producer gates before packaging",
    )
    args = parser.parse_args()

    source = Path(args.source_dir)
    if not source.is_absolute():
        source = REPO_ROOT / source
    source = source.resolve()

    pcs_core_root = None
    if args.validate_pcs_core_output is not None:
        raw = str(args.validate_pcs_core_output).strip()
        from sm_pipeline.benchmark.pcs_core_benchmark_validate import resolve_pcs_core_from_env

        pcs_core_root = (
            resolve_pcs_core_from_env(repo_root=REPO_ROOT)
            if raw == ""
            else resolve_pcs_core_root(raw, repo_root=REPO_ROOT)
        )
        if pcs_core_root is None:
            print("pcs-core root not found for pre-package validation", file=sys.stderr)
            return 1

    errors = validate_benchmark_output_dir(
        source,
        REPO_ROOT,
        pcs_core_root=pcs_core_root,
        release_grade=args.release_grade,
    )
    if errors:
        for msg in errors:
            print(msg, file=sys.stderr)
        return 1

    dest = Path(args.dest) if args.dest else Path(str(source) + "_bundle")
    if not dest.is_absolute():
        dest = REPO_ROOT / dest
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)

    for name in (*REQUIRED_FILES, "bench_suite_manifest.v0.json"):
        src_file = source / name
        if src_file.is_file():
            shutil.copy2(src_file, dest / name)

    for sidecar_name in (
        "explain_quality_reports",
        "coverage_reports",
        "benchmark_runs",
        "failure_localization_reports",
    ):
        sidecar_src = source / sidecar_name
        if sidecar_src.is_dir():
            shutil.copytree(sidecar_src, dest / sidecar_name)

    ingest = json.loads((source / PCS_BENCH_INGEST_FILENAME).read_text(encoding="utf-8"))
    suite_id = str(ingest.get("suite_id") or "")
    run_doc = json.loads((source / "benchmark_run.v0.json").read_text(encoding="utf-8"))
    manifest = build_run_suite_manifest(
        suite_id=suite_id,
        out_dir=dest,
        ingest_path=dest / PCS_BENCH_INGEST_FILENAME,
        passed=bool(run_doc.get("passed")),
    )
    (dest / "bench_suite_manifest.v0.json").write_text(
        json.dumps(manifest, indent=2) + "\n",
        encoding="utf-8",
    )

    readme = REPO_ROOT / "docs/pcs/bench-ingest-contract.md"
    if readme.is_file():
        shutil.copy2(readme, dest / "README.md")

    print(f"OK: packaged pcs-bench bundle -> {dest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
