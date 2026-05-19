"""PCS rendering benchmark runner and section coverage."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from sm_pipeline.benchmark.pcs_sections import (
    REQUIRED_INTERPRETABILITY_SECTIONS,
    evaluate_section_coverage,
    section_present,
)
from sm_pipeline.benchmark.rendering import (
    check_rendering_regression,
    discover_case_dirs,
    export_pcs_bench_payload,
    run_rendering_benchmark,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
BENCHMARKS = REPO_ROOT / "benchmarks" / "rendering"


def test_rendering_benchmark_cases_exist() -> None:
    case_dirs = discover_case_dirs(BENCHMARKS)
    names = {path.name for path in case_dirs}
    assert "labtrust_qc_release" in names
    assert "tool_use_safety" in names
    assert "computation_reproducibility" in names
    assert "rejected_certificate" in names


def test_interpretability_sections_count() -> None:
    assert len(REQUIRED_INTERPRETABILITY_SECTIONS) == 18


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
        "schema_version": "PcsRenderingBenchmarkReport.v0",
        "passed": True,
        "case_count": 1,
        "metrics": {"required_sections_rendered": 1.0},
        "failures": [],
    }
    payload = export_pcs_bench_payload(report)
    assert payload["benchmark"] == "pcs_rendering"
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
    assert (out / "rendering_benchmark_report.json").is_file()
    assert report["schema_version"] == "PcsRenderingBenchmarkReport.v0"
    assert report["pcs_bench"]["consumer"] == "pcs-bench"
