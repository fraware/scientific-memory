"""pcs-bench ingest contract and suite registry tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from sm_pipeline.benchmark.bench_registry import load_suite_registry, validate_suite_id
from sm_pipeline.benchmark.pcs_core_coverage import EXPLAIN_QUALITY_SECTION_IDS
from sm_pipeline.benchmark.report_builder import PCS_BENCH_INGEST_FILENAME, validate_benchmark_output_dir
from sm_pipeline.benchmark.rendering import run_rendering_benchmark
from sm_pipeline.pcs_validate.canonical_hash import canonical_hash

REPO_ROOT = Path(__file__).resolve().parents[2]
EXTERNAL_REVIEWER = REPO_ROOT / "benchmarks/rendering/external_reviewer_minimal"


def test_suite_registry_lists_rendering_suites() -> None:
    registry = load_suite_registry(REPO_ROOT)
    suite_ids = {row["suite_id"] for row in registry["suites"]}
    assert "scientific-memory-rendering-v0" in suite_ids
    assert "scientific-memory-external-reviewer-v0" in suite_ids
    contract = registry["ingest_contract"]
    assert contract["schema_version"] == "v0"
    assert set(contract["explain_quality_section_ids"]) == set(EXPLAIN_QUALITY_SECTION_IDS)
    assert "import_failed" in contract["failure_kinds"]


def test_unknown_suite_id_rejected() -> None:
    assert validate_suite_id(REPO_ROOT, "not-a-real-suite") is not None


def test_normalize_benchmark_out_dir_strips_out_prefix() -> None:
    from sm_pipeline.benchmark.report_builder import normalize_benchmark_out_dir

    assert normalize_benchmark_out_dir("OUT=benchmark_runs/foo") == "benchmark_runs/foo"
    assert normalize_benchmark_out_dir("benchmark_runs/foo") == "benchmark_runs/foo"


def test_ingest_canonical_shape_from_run(tmp_path: Path) -> None:
    out = tmp_path / "ingest_probe"
    run_rendering_benchmark(
        EXTERNAL_REVIEWER,
        repo_root=REPO_ROOT,
        out_dir=out,
        isolated=True,
    )
    ingest = json.loads((out / PCS_BENCH_INGEST_FILENAME).read_text(encoding="utf-8"))
    assert ingest["schema_version"] == "v0"
    assert ingest["producer_id"] == "scientific-memory"
    assert ingest["suite_id"] == "scientific-memory-external-reviewer-v0"
    assert ingest["benchmark_runs"]
    assert ingest["coverage_reports"]
    assert ingest["explain_quality_reports"]
    assert ingest["query_results"]
    assert ingest["rendering_reports"]
    assert ingest["signature_or_digest"] == canonical_hash(ingest)
    assert (out / "bench_suite_manifest.v0.json").is_file()
    assert validate_benchmark_output_dir(out, REPO_ROOT) == []
