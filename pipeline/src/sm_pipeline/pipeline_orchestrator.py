"""SPEC 8.1–8.7 stage orchestration; delegates to ingest/extract/formalize/publish modules."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from sm_pipeline.extract.claims import extract_claims as run_extract_claims
from sm_pipeline.extract.normalize import normalize_paper
from sm_pipeline.formalize.scaffold import scaffold_formal as run_scaffold_formal
from sm_pipeline.ingest.admit_paper import admit_paper
from sm_pipeline.ingest.build_index import build_index
from sm_pipeline.ingest.hash_source import hash_source_for_paper
from sm_pipeline.ingest.intake_report import write_intake_report
from sm_pipeline.models.stage_contracts import (
    PipelineRunReport,
    PipelineStage,
    StageOutcome,
    StageSeverity,
)
from sm_pipeline.publish.canonical import publish_paper_artifacts
from sm_pipeline.publish.export_portal_data import export_portal_data

StageHandler = Callable[[Path, str], StageOutcome]


def run_intake_stage(
    repo_root: Path, paper_id: str, *, admit_if_missing: bool = True
) -> StageOutcome:
    """8.1: admit paper skeleton, hash source, intake report, rebuild index."""
    repo_root = repo_root.resolve()
    paper_dir = repo_root / "corpus" / "papers" / paper_id
    if not paper_dir.is_dir() and admit_if_missing:
        admit_paper(repo_root, paper_id)
    elif not paper_dir.is_dir():
        return StageOutcome(
            stage=PipelineStage.intake,
            paper_id=paper_id,
            severity=StageSeverity.error,
            message=f"Paper directory missing: {paper_id}",
        )
    digest = hash_source_for_paper(repo_root, paper_id)
    intake_path = write_intake_report(repo_root, paper_id)
    build_index(repo_root)
    return StageOutcome(
        stage=PipelineStage.intake,
        paper_id=paper_id,
        severity=StageSeverity.ok,
        message="Intake: hash, intake_report, index updated",
        details={"sha256": digest, "intake_report": str(intake_path)},
    )


def run_extraction_stage(repo_root: Path, paper_id: str) -> StageOutcome:
    """8.2: extract claims (scaffold)."""
    repo_root = repo_root.resolve()
    run_extract_claims(repo_root, paper_id)
    return StageOutcome(
        stage=PipelineStage.extraction,
        paper_id=paper_id,
        severity=StageSeverity.ok,
        message="Extraction: extract-claims completed",
    )


def run_normalization_stage(repo_root: Path, paper_id: str) -> StageOutcome:
    """8.3: normalize symbols/assumptions/links."""
    out = normalize_paper(repo_root, paper_id)
    return StageOutcome(
        stage=PipelineStage.normalization,
        paper_id=paper_id,
        severity=StageSeverity.ok,
        message="Normalization completed",
        details=out,
    )


def run_formal_mapping_stage(repo_root: Path, paper_id: str) -> StageOutcome:
    """8.4: scaffold formal mapping and Lean stubs."""
    run_scaffold_formal(repo_root, paper_id)
    return StageOutcome(
        stage=PipelineStage.formal_mapping,
        paper_id=paper_id,
        severity=StageSeverity.ok,
        message="Formal mapping: scaffold-formal completed",
    )


def run_publication_stage(repo_root: Path, paper_id: str) -> StageOutcome:
    """8.7: publish manifest, theorem cards, and refresh portal export (canonical path)."""
    details = publish_paper_artifacts(repo_root, paper_id)
    return StageOutcome(
        stage=PipelineStage.publication,
        paper_id=paper_id,
        severity=StageSeverity.ok,
        message="Publication: manifest, theorem cards, portal export refreshed",
        details=details,
    )


def run_export_portal_bundle(repo_root: Path) -> StageOutcome:
    """Export canonical portal JSON bundle (post-publication artifact)."""
    out = export_portal_data(repo_root)
    return StageOutcome(
        stage=PipelineStage.publication,
        paper_id=None,
        severity=StageSeverity.ok,
        message="Portal export written",
        details={"path": str(out)},
    )


_DEFAULT_STAGE_HANDLERS: dict[PipelineStage, StageHandler] = {
    PipelineStage.intake: run_intake_stage,
    PipelineStage.extraction: run_extraction_stage,
    PipelineStage.normalization: run_normalization_stage,
    PipelineStage.formal_mapping: run_formal_mapping_stage,
    PipelineStage.publication: run_publication_stage,
}

_stage_handlers: dict[PipelineStage, StageHandler] = dict(_DEFAULT_STAGE_HANDLERS)


def register_pipeline_stage_handler(stage: PipelineStage, handler: StageHandler) -> None:
    """
    Override the callable used for a pipeline stage (tests or downstream extensions).

    Stages ``formalization`` and ``kernel_linkage`` are not registered; they are always
    emitted as skipped outcomes from ``run_pipeline_for_paper``.
    """
    if stage in (PipelineStage.formalization, PipelineStage.kernel_linkage):
        msg = f"Cannot register handler for manual stage {stage!r}"
        raise ValueError(msg)
    _stage_handlers[stage] = handler


def reset_pipeline_stage_handlers() -> None:
    """Restore default stage handlers (use in test teardown)."""
    _stage_handlers.clear()
    _stage_handlers.update(_DEFAULT_STAGE_HANDLERS)


def run_pipeline_for_paper(
    repo_root: Path,
    paper_id: str,
    *,
    stages: list[PipelineStage] | None = None,
) -> PipelineRunReport:
    """
    Run selected stages in order. Default: publication only (common CI/local path).
    Full local workflow can pass stages for intake through publication.
    """
    repo_root = repo_root.resolve()
    report = PipelineRunReport(repo_root=str(repo_root))
    order = stages or [PipelineStage.publication]
    for stage in order:
        if stage == PipelineStage.formalization:
            report.add(
                StageOutcome(
                    stage=PipelineStage.formalization,
                    paper_id=paper_id,
                    severity=StageSeverity.skipped,
                    message="Formalization is manual Lean work; use lake build after editing formal/",
                )
            )
        elif stage == PipelineStage.kernel_linkage:
            report.add(
                StageOutcome(
                    stage=PipelineStage.kernel_linkage,
                    paper_id=paper_id,
                    severity=StageSeverity.skipped,
                    message="Kernel linkage is manual (corpus/kernels.json, executable_links)",
                )
            )
        elif stage in _stage_handlers:
            report.add(_stage_handlers[stage](repo_root, paper_id))
        else:
            report.add(
                StageOutcome(
                    stage=stage,
                    paper_id=paper_id,
                    severity=StageSeverity.error,
                    message=f"No handler registered for stage {stage.value!r}",
                )
            )
    return report
