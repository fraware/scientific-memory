"""Unified validation gate runner (SPEC section 11): structured report + parity with validate_repo."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Callable

from pydantic import BaseModel, Field

from sm_pipeline.validate.coverage import validate_coverage
from sm_pipeline.validate.extraction_artifacts import validate_extraction_run_required
from sm_pipeline.validate.graph import validate_dependency_graph_bootstrap_warn, validate_graph
from sm_pipeline.validate.migration import validate_migration_doc
from sm_pipeline.validate.normalization import validate_normalization
from sm_pipeline.validate.provenance import validate_provenance
from sm_pipeline.validate.reviewer import validate_reviewer_lifecycle
from sm_pipeline.validate.snapshot_quality import validate_snapshot_quality
from sm_pipeline.validate.llm_proposals import validate_llm_proposal_sidecars_warn
from sm_pipeline.validate.theorem_card_reviewer import validate_theorem_card_reviewer


class GateStepResult(BaseModel):
    gate_id: str
    check_id: str
    status: str  # "ok" | "warn"
    message: str = ""


class GateReport(BaseModel):
    """Machine-readable report for CI and local tooling."""

    repo_root: str
    ok: bool = True
    steps: list[GateStepResult] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)

    def to_json_dict(self) -> dict[str, Any]:
        return self.model_dump(mode="json")


def _echo_recommendations(repo_root: Path) -> None:
    """Non-blocking hints: suggest DOI/arXiv when missing for papers with past year."""
    papers_dir = repo_root / "corpus" / "papers"
    index_path = repo_root / "corpus" / "index.json"
    if not index_path.exists():
        return
    index = json.loads(index_path.read_text(encoding="utf-8"))
    paper_list = index.get("papers") or []
    try:
        from datetime import datetime

        current_year = datetime.now().year
    except Exception:
        return
    for entry in paper_list:
        if not isinstance(entry, dict):
            continue
        paper_id = entry.get("id")
        year = entry.get("year")
        if not paper_id or not isinstance(year, (int, float)):
            continue
        if int(year) > current_year:
            continue
        meta_path = papers_dir / paper_id / "metadata.json"
        if not meta_path.exists():
            continue
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        if not isinstance(meta, dict):
            continue
        source = meta.get("source") or {}
        if source.get("doi") or source.get("arxiv_id"):
            continue
        msg = (
            f"Recommendation: paper {paper_id} has no DOI or arXiv ID; "
            "consider setting metadata.source.doi or metadata.source.arxiv_id"
        )
        print(msg, file=sys.stderr)


def run_all_gates(repo_root: Path) -> GateReport:
    """
    Run all validation checks in deterministic order (parity with legacy validate_repo).
    Raises on first failing check that previously raised.
    """
    from sm_pipeline.validate.schemas import validate_json_schemas_and_kernels

    repo_root = repo_root.resolve()
    report = GateReport(repo_root=str(repo_root))

    checks: list[tuple[str, str, Callable[[Path], None]]] = [
        ("gate2", "json_schemas_and_kernels", validate_json_schemas_and_kernels),
        ("gate2", "normalization_integrity", validate_normalization),
        ("gate3", "provenance_integrity", validate_provenance),
        ("gate2", "extraction_run_required", validate_extraction_run_required),
        ("gate2", "graph_integrity", validate_graph),
        ("gate2", "migration_doc", validate_migration_doc),
        ("gate2", "reviewer_lifecycle", validate_reviewer_lifecycle),
        ("gate2", "theorem_card_reviewer", validate_theorem_card_reviewer),
        ("gate4", "coverage_integrity", validate_coverage),
    ]

    for gate_id, check_id, fn in checks:
        fn(repo_root)
        report.steps.append(GateStepResult(gate_id=gate_id, check_id=check_id, status="ok"))

    snapshot_warnings = validate_snapshot_quality(repo_root)
    for w in snapshot_warnings:
        report.warnings.append(w)
        print(f"Snapshot quality (warn): {w}", file=sys.stderr)
        report.steps.append(
            GateStepResult(
                gate_id="gate2",
                check_id="snapshot_quality",
                status="warn",
                message=w,
            )
        )

    dep_bootstrap_warnings = validate_dependency_graph_bootstrap_warn(repo_root)
    for w in dep_bootstrap_warnings:
        report.warnings.append(w)
        print(f"Dependency graph (warn): {w}", file=sys.stderr)
        report.steps.append(
            GateStepResult(
                gate_id="gate2",
                check_id="dependency_graph_bootstrap",
                status="warn",
                message=w,
            )
        )

    llm_warnings = validate_llm_proposal_sidecars_warn(repo_root)
    for w in llm_warnings:
        report.warnings.append(w)
        print(f"Suggestion sidecar (warn): {w}", file=sys.stderr)
        report.steps.append(
            GateStepResult(
                gate_id="gate2",
                check_id="suggestion_sidecars",
                status="warn",
                message=w,
            )
        )

    _echo_recommendations(repo_root)
    return report


