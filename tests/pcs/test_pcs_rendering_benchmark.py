"""PCS rendering benchmark runner and section coverage."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from sm_pipeline.benchmark.pcs_sections import (
    BENCHMARK_RENDERING_SECTIONS,
    REQUIRED_INTERPRETABILITY_SECTIONS,
    evaluate_section_coverage,
    section_present,
)
from sm_pipeline.benchmark.report_builder import (
    PCS_BENCH_INGEST_FILENAME,
    build_v0_reports,
    validate_benchmark_output_dir,
    validate_v0_reports,
)
from sm_pipeline.benchmark.rendering import (
    check_rendering_regression,
    discover_case_dirs,
    export_pcs_bench_payload,
    run_rendering_benchmark,
)

V0_REPORT_FILES = (
    "benchmark_run.v0.json",
    "rendering_coverage_report.v0.json",
    "query_coverage_report.v0.json",
    "failed_release_rendering_report.v0.json",
)

REPO_ROOT = Path(__file__).resolve().parents[2]
BENCHMARKS = REPO_ROOT / "benchmarks" / "rendering"


def test_rendering_benchmark_cases_exist() -> None:
    case_dirs = discover_case_dirs(BENCHMARKS)
    names = {path.name for path in case_dirs}
    assert "labtrust_qc_release" in names
    assert "tool_use_safety" in names
    assert "computation_reproducibility" in names
    assert "formal_trust_kernel" in names
    assert "rejected_certificate" in names
    assert "result_hash_mismatch" in names


def test_interpretability_sections_count() -> None:
    assert len(REQUIRED_INTERPRETABILITY_SECTIONS) == 18
    assert len(BENCHMARK_RENDERING_SECTIONS) == 17
    assert "Assumptions" not in BENCHMARK_RENDERING_SECTIONS
    assert "Formal Trust Kernel" in BENCHMARK_RENDERING_SECTIONS


def test_canonical_read_model_covers_interpretability_sections() -> None:
    read_model = json.loads(
        (REPO_ROOT / "tests" / "pcs" / "fixtures" / "canonical_pcs_read_model.json").read_text(
            encoding="utf-8",
        ),
    )
    report = evaluate_section_coverage(read_model)
    assert report["missing_sections"] == []
    assert section_present(read_model, "Formal Trust Kernel")


def test_export_pcs_bench_payload_shape() -> None:
    report = {
        "benchmark": "pcs_rendering",
        "schema_version": "BenchmarkRun.v0",
        "v0_reports": {"benchmark_run.v0.json": "x"},
        "passed": True,
        "case_count": 1,
        "metrics": {"required_sections_rendered": 1.0},
        "failures": [],
    }
    payload = export_pcs_bench_payload(report)
    assert payload["benchmark"] == "pcs_rendering"
    assert payload["schema_version"] == "PcsBenchIngest.v0"
    assert payload["ingest_manifest"] == PCS_BENCH_INGEST_FILENAME
    assert payload["metrics"]["required_sections_rendered"] == 1.0


def test_rendering_regression_thresholds_pass_after_successful_run(tmp_path: Path) -> None:
    report = run_rendering_benchmark(
        BENCHMARKS / "labtrust_qc_release",
        repo_root=REPO_ROOT,
        out_dir=tmp_path / "regression_probe",
        isolated=True,
    )
    ok, msg = check_rendering_regression(REPO_ROOT, report)
    assert ok, msg


def test_labtrust_rendering_benchmark_passes(tmp_path: Path) -> None:
    out = tmp_path / "labtrust_rendering"
    report = run_rendering_benchmark(
        BENCHMARKS / "labtrust_qc_release",
        repo_root=REPO_ROOT,
        out_dir=out,
        isolated=True,
    )
    assert report["passed"] is True, report.get("failures")
    for name in V0_REPORT_FILES:
        assert (out / name).is_file(), name
    assert report["schema_version"] == "BenchmarkRun.v0"
    assert report["pcs_bench"]["consumer"] == "pcs-bench"
    assert (out / PCS_BENCH_INGEST_FILENAME).is_file()
    assert (out / "pcs_bench_payload.json").is_file()
    assert validate_benchmark_output_dir(out, REPO_ROOT) == []


def test_v0_report_builder_schema_valid() -> None:
    case_results = [
        {
            "case_id": "labtrust_qc_release",
            "claim_id": "claim-pcs-qc-release-v0.1",
            "release_id": "release-pcs-v0.1-labtrust-qc",
            "failure_mode": False,
            "passed": True,
            "failures": [],
            "section_coverage": {"required_sections_rendered": 1.0},
            "metrics": {"required_sections_rendered": 1.0},
            "queries": {"passed": True, "queries": []},
            "compare": {"skipped": True},
        },
    ]
    reports = build_v0_reports(
        case_results,
        repo_root=REPO_ROOT,
        cases_path=BENCHMARKS / "labtrust_qc_release",
        aggregate_failures=[],
        metrics={"required_sections_rendered": 1.0},
    )
    assert validate_v0_reports(REPO_ROOT, reports) == []


def test_full_rendering_benchmark_suite_passes(tmp_path: Path) -> None:
    """All 10 rendering cases (4 success + 6 failed) with v0 schema validation."""
    out = tmp_path / "pcs_rendering_full"
    report = run_rendering_benchmark(
        BENCHMARKS,
        repo_root=REPO_ROOT,
        out_dir=out,
        isolated=True,
    )
    assert report["case_count"] == 10, report.get("case_count")
    assert report["passed"] is True, report.get("failures")
    assert validate_benchmark_output_dir(out, REPO_ROOT) == []
    ok, msg = check_rendering_regression(REPO_ROOT, report)
    assert ok, msg
    ingest = json.loads((out / PCS_BENCH_INGEST_FILENAME).read_text(encoding="utf-8"))
    assert ingest["consumer"] == "pcs-bench"
    assert len(ingest.get("ingest_files") or []) >= 4
    for name in ingest.get("ingest_files") or []:
        path = Path(ingest["artifacts"][name])
        assert path.is_file(), name
