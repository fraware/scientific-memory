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
        default="",
        help="Destination bundle directory (default: <source>_bundle)",
    )
    args = parser.parse_args()

    source = Path(args.source_dir)
    if not source.is_absolute():
        source = REPO_ROOT / source
    source = source.resolve()

    errors = validate_benchmark_output_dir(source, REPO_ROOT)
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

    for name in REQUIRED_FILES:
        src_file = source / name
        if src_file.is_file():
            shutil.copy2(src_file, dest / name)

    ingest = json.loads((source / PCS_BENCH_INGEST_FILENAME).read_text(encoding="utf-8"))
    suite_id = str(ingest.get("suite_id") or "")
    manifest = build_run_suite_manifest(
        suite_id=suite_id,
        out_dir=dest,
        ingest_path=dest / PCS_BENCH_INGEST_FILENAME,
        passed=bool(ingest.get("passed")),
    )
    (dest / "bench_suite_manifest.v0.json").write_text(
        json.dumps(manifest, indent=2) + "\n",
        encoding="utf-8",
    )

    readme = REPO_ROOT / "docs/pcs-bench-ingest.md"
    if readme.is_file():
        shutil.copy2(readme, dest / "README.md")

    print(f"OK: packaged pcs-bench bundle -> {dest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
