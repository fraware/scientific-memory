"""PCS rendering benchmark runner and section coverage."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from sm_pipeline.benchmark.failure_taxonomy import FAILURE_KINDS
from sm_pipeline.benchmark.pcs_core_coverage import EXPLAIN_QUALITY_SECTION_IDS, suite_id_for_cases_path
from sm_pipeline.benchmark.pcs_sections import (
    BENCHMARK_RENDERING_SECTIONS,
    REQUIRED_INTERPRETABILITY_SECTIONS,
    evaluate_section_coverage,
    section_present,
)
from sm_pipeline.benchmark.report_builder import (
    EXPLAIN_QUALITY_REPORT_FILENAME,
    PCS_BENCH_INGEST_FILENAME,
    V0_REPORT_FILENAMES,
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

REPO_ROOT = Path(__file__).resolve().parents[2]
BENCHMARKS = REPO_ROOT / "benchmarks" / "rendering"
EXTERNAL_REVIEWER = BENCHMARKS / "external_reviewer_minimal"

REQUIRED_ARTIFACTS = (
    *V0_REPORT_FILENAMES,
    EXPLAIN_QUALITY_REPORT_FILENAME,
    PCS_BENCH_INGEST_FILENAME,
)


def test_rendering_benchmark_cases_exist() -> None:
    case_dirs = discover_case_dirs(BENCHMARKS)
    names = {path.name for path in case_dirs}
    assert "labtrust_qc_release" in names
    assert "formal_trust_kernel" in names
    assert "result_hash_mismatch" in names
    reviewer = discover_case_dirs(EXTERNAL_REVIEWER)
    reviewer_names = {path.name for path in reviewer}
    assert reviewer_names == {
        "labtrust_valid",
        "failed_lean",
        "stale_release",
        "result_hash_mismatch",
        "release_compare",
    }


def test_interpretability_sections_count() -> None:
    assert len(REQUIRED_INTERPRETABILITY_SECTIONS) == 18
    assert len(BENCHMARK_RENDERING_SECTIONS) == 17
    assert len(EXPLAIN_QUALITY_SECTION_IDS) == 8


def test_canonical_read_model_covers_interpretability_sections() -> None:
    read_model = json.loads(
        (REPO_ROOT / "tests" / "pcs" / "fixtures" / "canonical_pcs_read_model.json").read_text(
            encoding="utf-8",
        ),
    )
    report = evaluate_section_coverage(read_model)
    assert report["missing_sections"] == []
    assert section_present(read_model, "Formal Trust Kernel")


def test_pcs_bench_ingest_schema_shape() -> None:
    ingest = {
        "schema_version": "v0",
        "producer_id": "scientific-memory",
        "suite_id": "scientific-memory-rendering-v0",
        "workflow_id": "pcs.scientific_memory",
        "benchmark_runs": [{"benchmark_run_id": "pcs_rendering", "path": "/tmp/run.json", "passed": True}],
        "coverage_reports": [
            {
                "coverage_report_id": "rendering-coverage",
                "path": "/tmp/coverage.json",
                "explain_quality_section_ids": list(EXPLAIN_QUALITY_SECTION_IDS),
            },
        ],
        "explain_quality_reports": [],
        "query_results": [{"query_report_id": "query-coverage", "path": "/tmp/query.json"}],
        "rendering_reports": [{"rendering_report_id": "failed-release-rendering", "path": "/tmp/failed.json"}],
        "source_repo": "https://github.com/fraware/scientific-memory",
        "source_commit": "abc123",
        "signature_or_digest": "sha256:" + "a" * 64,
    }
    errors = validate_v0_reports(REPO_ROOT, {PCS_BENCH_INGEST_FILENAME: ingest})
    assert errors == []


def test_export_pcs_bench_payload_shape() -> None:
    report = {
        "suite_id": "scientific-memory-rendering-v0",
        "passed": True,
        "case_count": 1,
        "generated_at": "2026-01-01T00:00:00Z",
        "metrics": {"required_sections_rendered": 1.0},
        "failures": [],
        "v0_reports": {"benchmark_run.v0.json": "x"},
    }
    payload = export_pcs_bench_payload(report)
    assert payload["schema_version"] == "v0"
    assert payload["producer_id"] == "scientific-memory"
    assert payload["ingest_manifest"] == PCS_BENCH_INGEST_FILENAME


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
    for name in REQUIRED_ARTIFACTS:
        assert (out / name).is_file(), name
    ingest = json.loads((out / PCS_BENCH_INGEST_FILENAME).read_text(encoding="utf-8"))
    assert ingest["schema_version"] == "v0"
    assert ingest["producer_id"] == "scientific-memory"
    assert ingest["workflow_id"] == "pcs.scientific_memory"
    assert ingest["benchmark_runs"]
    assert ingest["coverage_reports"]
    assert validate_benchmark_output_dir(out, REPO_ROOT) == []


def test_failed_lean_case_emits_formal_failed_kind(tmp_path: Path) -> None:
    report = run_rendering_benchmark(
        BENCHMARKS / "failed" / "failed_lean_check",
        repo_root=REPO_ROOT,
        out_dir=tmp_path / "failed_lean_taxonomy",
        isolated=True,
    )
    case = report["cases"][0]
    assert case["passed"] is True
    kinds = case.get("failure_kinds") or {}
    assert kinds.get("formal_failed") is False


def test_failure_kinds_taxonomy_on_cases(tmp_path: Path) -> None:
    report = run_rendering_benchmark(
        BENCHMARKS / "failed" / "failed_lean_check",
        repo_root=REPO_ROOT,
        out_dir=tmp_path / "failed_lean_case",
        isolated=True,
    )
    case = report["cases"][0]
    assert set(case["failure_kinds"]) == set(FAILURE_KINDS)
    for event in case.get("failure_events") or []:
        assert event.get("kind") in FAILURE_KINDS
        assert event.get("responsible_component")
        assert "repair_hint" in event


def test_external_reviewer_minimal_suite(tmp_path: Path) -> None:
    out = tmp_path / "external_reviewer"
    report = run_rendering_benchmark(
        EXTERNAL_REVIEWER,
        repo_root=REPO_ROOT,
        out_dir=out,
        isolated=True,
    )
    assert report["case_count"] == 5, report.get("case_count")
    assert report["suite_id"] == "scientific-memory-external-reviewer-v0"
    assert report["passed"] is True, report.get("failures")
    ingest = json.loads((out / PCS_BENCH_INGEST_FILENAME).read_text(encoding="utf-8"))
    assert ingest["suite_id"] == "scientific-memory-external-reviewer-v0"
    coverage = json.loads((out / "rendering_coverage_report.v0.json").read_text(encoding="utf-8"))
    assert coverage["explain_quality_section_ids"] == list(EXPLAIN_QUALITY_SECTION_IDS)
    assert validate_benchmark_output_dir(out, REPO_ROOT) == []


def test_full_rendering_benchmark_suite_passes(tmp_path: Path) -> None:
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


def test_v0_report_builder_schema_valid() -> None:
    case_results = [
        {
            "case_id": "labtrust_qc_release",
            "claim_id": "claim-pcs-qc-release-v0.1",
            "release_id": "release-pcs-v0.1-labtrust-qc",
            "failure_mode": False,
            "import_failed": False,
            "passed": True,
            "failures": [],
            "failure_events": [],
            "read_model": json.loads(
                (REPO_ROOT / "tests" / "pcs" / "fixtures" / "canonical_pcs_read_model.json").read_text(
                    encoding="utf-8",
                ),
            ),
            "section_coverage": {"present_sections": list(BENCHMARK_RENDERING_SECTIONS)},
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
    for kind in FAILURE_KINDS:
        assert kind  # taxonomy stable

    assert suite_id_for_cases_path(str(EXTERNAL_REVIEWER)) == "scientific-memory-external-reviewer-v0"
