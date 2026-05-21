"""pcs-core benchmark output validation helpers."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from sm_pipeline.benchmark.failure_taxonomy import (
    classify_failure_evidence_kind,
    classify_section_failure_kind,
)
from sm_pipeline.benchmark.pcs_core_benchmark_validate import (
    resolve_pcs_core_from_env,
    resolve_pcs_core_root,
    validate_benchmark_artifacts_with_pcs_core,
)
from sm_pipeline.benchmark.rendering import run_rendering_benchmark
from sm_pipeline.benchmark.report_builder import PCS_WORKFLOW_ID

REPO_ROOT = Path(__file__).resolve().parents[2]
EXTERNAL_REVIEWER = REPO_ROOT / "benchmarks/rendering/external_reviewer_minimal"


def test_classify_section_failure_kind_formal_only() -> None:
    assert classify_section_failure_kind(["Formal Trust Kernel"]) == "formal_failed"
    assert classify_section_failure_kind(["Claim", "Lineage"]) == "render_failed"


def test_classify_failure_evidence_kind_formal() -> None:
    read_model = {
        "formal_trust_kernel": {
            "lean_check_results": [{"result": "failed", "lean_theorem": "T"}],
        },
    }
    assert classify_failure_evidence_kind(read_model, {}) == "formal_failed"
    assert classify_failure_evidence_kind(read_model, {"failure_kind": "render_failed"}) == "render_failed"


def test_resolve_pcs_core_root_explicit(tmp_path: Path) -> None:
    (tmp_path / "schemas").mkdir()
    assert resolve_pcs_core_root(tmp_path, repo_root=REPO_ROOT) == tmp_path.resolve()


def test_resolve_pcs_core_from_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    (tmp_path / "schemas").mkdir()
    monkeypatch.setenv("PCS_CORE_PATH", str(tmp_path))
    assert resolve_pcs_core_from_env(repo_root=REPO_ROOT) == tmp_path.resolve()


def test_validate_against_pcs_core_mirror_schemas(tmp_path: Path) -> None:
    pcs_core = tmp_path / "pcs-core"
    schemas = pcs_core / "schemas" / "benchmark"
    schemas.mkdir(parents=True)
    sm_schema_dir = REPO_ROOT / "schemas" / "pcs" / "benchmark"
    for name in (
        "BenchmarkRun.v0.schema.json",
        "RenderingCoverageReport.v0.schema.json",
        "QueryCoverageReport.v0.schema.json",
        "FailedReleaseRenderingReport.v0.schema.json",
        "ExplainQualityReport.v0.schema.json",
        "PcsBenchIngest.v0.schema.json",
    ):
        src = sm_schema_dir / name
        if src.is_file():
            (schemas / name).write_text(src.read_text(encoding="utf-8"), encoding="utf-8")

    out = tmp_path / "bench_out"
    run_rendering_benchmark(
        EXTERNAL_REVIEWER,
        repo_root=REPO_ROOT,
        out_dir=out,
        isolated=True,
        validate_pcs_core_output=str(pcs_core),
    )

    reports = {
        path.name: json.loads(path.read_text(encoding="utf-8"))
        for path in out.glob("*.json")
        if path.name.endswith(".json")
    }
    errors = validate_benchmark_artifacts_with_pcs_core(reports, pcs_core)
    assert errors == [], errors


def test_workflow_id_constant() -> None:
    assert PCS_WORKFLOW_ID == "pcs.scientific_memory"
