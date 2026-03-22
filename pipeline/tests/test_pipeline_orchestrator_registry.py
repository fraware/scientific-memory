"""Registry extension points for pipeline stage orchestration."""

from __future__ import annotations

from pathlib import Path

import pytest

from sm_pipeline.models.stage_contracts import PipelineStage, StageOutcome, StageSeverity
from sm_pipeline.pipeline_orchestrator import (
    register_pipeline_stage_handler,
    reset_pipeline_stage_handlers,
    run_pipeline_for_paper,
)


def test_register_pipeline_stage_rejects_manual_stages() -> None:
    def _noop(_root: Path, _pid: str) -> StageOutcome:
        return StageOutcome(
            stage=PipelineStage.formalization,
            paper_id=_pid,
            severity=StageSeverity.ok,
            message="noop",
        )

    with pytest.raises(ValueError, match="Cannot register handler"):
        register_pipeline_stage_handler(PipelineStage.formalization, _noop)
    with pytest.raises(ValueError, match="Cannot register handler"):
        register_pipeline_stage_handler(PipelineStage.kernel_linkage, _noop)


def test_custom_stage_handler_invoked(tmp_path: Path) -> None:
    seen: list[str] = []

    def stub(_root: Path, pid: str) -> StageOutcome:
        seen.append(pid)
        return StageOutcome(
            stage=PipelineStage.publication,
            paper_id=pid,
            severity=StageSeverity.ok,
            message="stub-publication",
        )

    register_pipeline_stage_handler(PipelineStage.publication, stub)
    try:
        report = run_pipeline_for_paper(tmp_path, "paper_x", stages=[PipelineStage.publication])
        assert seen == ["paper_x"]
        assert len(report.outcomes) == 1
        assert report.outcomes[0].message == "stub-publication"
    finally:
        reset_pipeline_stage_handlers()


def test_reset_allows_fresh_registration(tmp_path: Path) -> None:
    def make_outcome(msg: str) -> StageOutcome:
        return StageOutcome(
            stage=PipelineStage.publication,
            paper_id="p",
            severity=StageSeverity.ok,
            message=msg,
        )

    register_pipeline_stage_handler(
        PipelineStage.publication,
        lambda _r, pid: make_outcome("first"),
    )
    try:
        r1 = run_pipeline_for_paper(tmp_path, "p", stages=[PipelineStage.publication])
        assert r1.outcomes[0].message == "first"
    finally:
        reset_pipeline_stage_handlers()

    register_pipeline_stage_handler(
        PipelineStage.publication,
        lambda _r, pid: make_outcome("second"),
    )
    try:
        r2 = run_pipeline_for_paper(tmp_path, "p", stages=[PipelineStage.publication])
        assert r2.outcomes[0].message == "second"
    finally:
        reset_pipeline_stage_handlers()
