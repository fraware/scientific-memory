"""Release-grade PCS benchmark producer gate tests."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from sm_pipeline.benchmark.failure_taxonomy import FAILURE_KINDS
from sm_pipeline.benchmark.pcs_core_ingest import (
    RELEASE_GRADE_COVERAGE_THRESHOLDS,
    UNKNOWN_COMMIT,
    _coverage_from_cases,
    _expected_responsible_component,
    build_coverage_report,
    build_producer_commands,
    validate_release_grade_coverage_adequacy,
    validate_release_grade_ingest,
    validate_release_grade_source_commit,
)
from sm_pipeline.benchmark.report_builder import PCS_BENCH_INGEST_FILENAME, validate_pcs_bench_ingest_file
from sm_pipeline.benchmark.rendering import run_rendering_benchmark

REPO_ROOT = Path(__file__).resolve().parents[2]
EXTERNAL_REVIEWER = REPO_ROOT / "benchmarks/rendering/external_reviewer_minimal"
LABTRUST = REPO_ROOT / "benchmarks/rendering/labtrust_qc_release"
REAL_COMMIT = "a" * 40


def test_build_producer_commands_includes_paths() -> None:
    commands = build_producer_commands(
        cases_path="benchmarks/rendering/labtrust_qc_release",
        out_dir="benchmark_runs/labtrust_rendering",
        pcs_core_path="../pcs-core",
        release_grade=True,
        passed=True,
    )
    assert len(commands) == 1
    assert "pcs-benchmark-rendering" in commands[0]["command"]
    assert "--release-grade" in commands[0]["command"]
    assert commands[0]["exit_code"] == 0


def test_expected_responsible_component_formal_failed() -> None:
    assert _expected_responsible_component({"failure_mode": True}, "formal_failed") == "formal_kernel"
    assert (
        _expected_responsible_component(
            {"expected_responsible_component": "scientific_memory"},
            "formal_failed",
        )
        == "scientific_memory"
    )


def test_validate_release_grade_rejects_zero_commit() -> None:
    assert validate_release_grade_source_commit(UNKNOWN_COMMIT)
    assert not validate_release_grade_source_commit(REAL_COMMIT)


def test_not_applicable_coverage_skips_threshold() -> None:
    na = _coverage_from_cases(
        coverage_id="suite-failed",
        metric="failure_localization",
        sm_metric="failed_release_rendering",
        cases=[],
        source_commit=REAL_COMMIT,
    )
    assert na["coverage_ratio"] == 1.0
    assert na["details"]["applicability"] == "not_applicable"
    errors = validate_release_grade_coverage_adequacy([na])
    assert not any("failed_release_rendering" in msg and "below threshold" in msg for msg in errors)


def test_validate_release_grade_coverage_thresholds() -> None:
    reports = [
        build_coverage_report(
            coverage_id="x-interpretability",
            metric="scientific_memory_interpretability",
            numerator=94,
            denominator=100,
            source_commit=REAL_COMMIT,
            details={"sm_metric": "scientific_memory_interpretability"},
        ),
        build_coverage_report(
            coverage_id="x-query",
            metric="scientific_memory_interpretability",
            numerator=100,
            denominator=100,
            source_commit=REAL_COMMIT,
            details={"sm_metric": "query_correctness"},
        ),
    ]
    for sm_metric in RELEASE_GRADE_COVERAGE_THRESHOLDS:
        if sm_metric in {"scientific_memory_interpretability", "query_correctness"}:
            continue
        reports.append(
            build_coverage_report(
                coverage_id=f"x-{sm_metric}",
                metric="scientific_memory_interpretability",
                numerator=100,
                denominator=100,
                source_commit=REAL_COMMIT,
                details={"sm_metric": sm_metric},
            ),
        )
    errors = validate_release_grade_coverage_adequacy(reports)
    assert any("scientific_memory_interpretability" in msg for msg in errors)
    assert not any("query_correctness" in msg for msg in errors)


def test_producer_gate_script_runs_external_reviewer(tmp_path: Path) -> None:
    import subprocess
    import sys

    pcs_core = REPO_ROOT.parent / "pcs-core"
    if not pcs_core.is_dir():
        pytest.skip("pcs-core checkout not adjacent")
    out = tmp_path / "gate_external"
    proc = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "scripts/run_pcs_bench_producer_gate.py"),
            "--cases",
            "benchmarks/rendering/external_reviewer_minimal",
            "--out",
            str(out),
            "--pcs-core",
            str(pcs_core),
            "--skip-pcs-bench-cli",
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr or proc.stdout


def test_release_grade_run_fails_without_real_commit(tmp_path: Path) -> None:
    with patch(
        "sm_pipeline.benchmark.report_builder.resolve_source_commit",
        return_value=UNKNOWN_COMMIT,
    ):
        report = run_rendering_benchmark(
            EXTERNAL_REVIEWER,
            repo_root=REPO_ROOT,
            out_dir=tmp_path / "zero_commit",
            isolated=True,
            release_grade=True,
            validate_pcs_core_output="",
        )
    assert not report.get("passed")
    assert any("source_commit" in str(msg) for msg in (report.get("failures") or []))


@pytest.mark.skipif(
    not (REPO_ROOT.parent / "pcs-core").is_dir(),
    reason="pcs-core checkout not adjacent",
)
def test_release_grade_labtrust_single_case_passes(tmp_path: Path) -> None:
    pcs_core = REPO_ROOT.parent / "pcs-core"
    out = tmp_path / "labtrust_producer"
    report = run_rendering_benchmark(
        LABTRUST,
        repo_root=REPO_ROOT,
        out_dir=out,
        isolated=True,
        release_grade=True,
        validate_pcs_core_output=str(pcs_core),
    )
    assert report.get("passed"), report.get("failures")


@pytest.mark.skipif(
    not (REPO_ROOT.parent / "pcs-core").is_dir(),
    reason="pcs-core checkout not adjacent",
)
def test_release_grade_external_reviewer_passes_with_real_commit(tmp_path: Path) -> None:
    pcs_core = REPO_ROOT.parent / "pcs-core"
    out = tmp_path / "release_grade"
    report = run_rendering_benchmark(
        EXTERNAL_REVIEWER,
        repo_root=REPO_ROOT,
        out_dir=out,
        isolated=True,
        release_grade=True,
        validate_pcs_core_output=str(pcs_core),
    )
    assert report.get("passed"), report.get("failures")
    ingest = json.loads((out / PCS_BENCH_INGEST_FILENAME).read_text(encoding="utf-8"))
    assert ingest["source_commit"] != UNKNOWN_COMMIT
    assert validate_release_grade_ingest(ingest, out_dir=out) == []
    manifest = json.loads((out / "bench_suite_manifest.v0.json").read_text(encoding="utf-8"))
    ref_paths = manifest.get("artifact_ref_paths") or []
    assert ref_paths
    assert any("explain_quality_reports/" in path for path in ref_paths)
    commands = ingest.get("commands") or []
    assert commands and "pcs-benchmark-rendering" in commands[0]["command"]
    fl_rows = ingest.get("failure_localization_reports") or []
    formal = next((row for row in fl_rows if row.get("case_id") == "failed_lean"), None)
    assert formal is not None
    assert formal["expected_failure_code"] == "formal_failed"
    assert formal["expected_responsible_component"] == "formal_kernel"
    assert formal["localized_correctly"] is True
    for run in ingest.get("benchmark_runs") or []:
        if run.get("scientific_memory_import_status") == "passed":
            assert run.get("system_admission_outcome") == "admitted"
    assert ingest.get("logs") == ["rendering_benchmark_summary.md"]
    observed_failure_codes = {row.get("expected_failure_code") for row in fl_rows}
    assert "formal_failed" in observed_failure_codes
    assert "staleness_failed" in observed_failure_codes
    assert observed_failure_codes <= set(FAILURE_KINDS)
    assert validate_pcs_bench_ingest_file(
        out / PCS_BENCH_INGEST_FILENAME,
        REPO_ROOT,
        pcs_core_root=pcs_core,
        release_grade=True,
    ) == []
