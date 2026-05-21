"""Embedded PcsBenchIngest.v0 and pcs-core semantic contract tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from sm_pipeline.benchmark.pcs_core_benchmark_validate import (
    _validate_pcs_bench_ingest_semantics,
    resolve_pcs_core_root,
    validate_benchmark_artifacts_with_pcs_core,
)
from sm_pipeline.benchmark.pcs_core_ingest import (
    EXPLAIN_QUALITY_SIDECARS_DIR,
    build_artifact_refs_for_ingest,
    build_embedded_pcs_bench_ingest,
    explain_quality_sidecar_relpath,
)
from sm_pipeline.benchmark.report_builder import PCS_BENCH_INGEST_FILENAME
from sm_pipeline.benchmark.rendering import run_rendering_benchmark

REPO_ROOT = Path(__file__).resolve().parents[2]
EXTERNAL_REVIEWER = REPO_ROOT / "benchmarks/rendering/external_reviewer_minimal"
PCS_CORE = REPO_ROOT.parent / "pcs-core"


def test_explain_quality_sidecar_paths_unique() -> None:
    a = explain_quality_sidecar_relpath("explain-quality-a")
    b = explain_quality_sidecar_relpath("explain-quality-b")
    assert a != b
    assert a.startswith(f"{EXPLAIN_QUALITY_SIDECARS_DIR}/")


def test_artifact_refs_cover_explain_quality_digests() -> None:
    commit = "a" * 40
    report = {
        "schema_version": "v0",
        "report_id": "explain-quality-probe",
        "suite_id": "scientific-memory-rendering-v0",
        "case_id": "probe",
        "producer_id": "scientific-memory",
        "workflow_id": "pcs.scientific_memory",
        "required_sections": ["provenance"],
        "sections": {"provenance": {"present": True, "score": 1.0}},
        "sections_present_count": 1,
        "sections_required_count": 1,
        "quality_score": 1.0,
        "gaps": [],
        "source_repo": "https://github.com/fraware/scientific-memory",
        "source_commit": commit,
        "signature_or_digest": "sha256:" + "b" * 64,
    }
    refs = build_artifact_refs_for_ingest(
        explain_quality_reports=[report],
        source_commit=commit,
    )
    assert len(refs) == 1
    assert refs[0]["artifact_type"] == "ExplainQualityReport.v0"
    assert refs[0]["sha256"] == report["signature_or_digest"]
    assert refs[0]["path"] == explain_quality_sidecar_relpath("explain-quality-probe")


@pytest.mark.skipif(not PCS_CORE.is_dir(), reason="pcs-core checkout not adjacent")
def test_external_reviewer_ingest_passes_pcs_core_schema_and_semantics(tmp_path: Path) -> None:
    out = tmp_path / "embedded_ingest"
    run_rendering_benchmark(
        EXTERNAL_REVIEWER,
        repo_root=REPO_ROOT,
        out_dir=out,
        isolated=True,
        validate_pcs_core_output=str(PCS_CORE),
    )
    ingest = json.loads((out / PCS_BENCH_INGEST_FILENAME).read_text(encoding="utf-8"))
    assert ingest.get("artifact_refs")
    assert len(ingest["artifact_refs"]) == len(ingest["explain_quality_reports"])
    sidecar_dir = out / EXPLAIN_QUALITY_SIDECARS_DIR
    assert sidecar_dir.is_dir()
    assert len(list(sidecar_dir.glob("*.v0.json"))) == len(ingest["explain_quality_reports"])

    reports = {PCS_BENCH_INGEST_FILENAME: ingest}
    schema_errors = validate_benchmark_artifacts_with_pcs_core(reports, PCS_CORE.resolve())
    assert schema_errors == [], schema_errors
    semantic_errors = _validate_pcs_bench_ingest_semantics(ingest)
    assert semantic_errors == [], semantic_errors


@pytest.mark.skipif(not PCS_CORE.is_dir(), reason="pcs-core checkout not adjacent")
def test_pcs_core_validate_artifact_accepts_sm_ingest(tmp_path: Path) -> None:
    pytest.importorskip("pcs_core")
    from pcs_core.validate import validate_artifact

    out = tmp_path / "pcs_core_ingest"
    run_rendering_benchmark(
        EXTERNAL_REVIEWER,
        repo_root=REPO_ROOT,
        out_dir=out,
        isolated=True,
    )
    ingest = json.loads((out / PCS_BENCH_INGEST_FILENAME).read_text(encoding="utf-8"))
    validate_artifact(ingest, "PcsBenchIngest.v0")


def test_resolve_pcs_core_sibling() -> None:
    if PCS_CORE.is_dir():
        assert resolve_pcs_core_root(PCS_CORE, repo_root=REPO_ROOT) == PCS_CORE.resolve()
