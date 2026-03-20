"""Typed stage contracts for SPEC 8.1–8.7 pipeline steps (orchestration boundary)."""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class PipelineStage(str, Enum):
    """Logical pipeline stages aligned with SPEC section 8."""

    intake = "intake"  # 8.1
    extraction = "extraction"  # 8.2
    normalization = "normalization"  # 8.3
    formal_mapping = "formal_mapping"  # 8.4
    formalization = "formalization"  # 8.5
    kernel_linkage = "kernel_linkage"  # 8.6
    publication = "publication"  # 8.7


class StageSeverity(str, Enum):
    ok = "ok"
    skipped = "skipped"
    error = "error"


class StageOutcome(BaseModel):
    """Result of running a single stage for one paper (or repo-wide where noted)."""

    stage: PipelineStage
    paper_id: str | None = None
    severity: StageSeverity = StageSeverity.ok
    message: str = ""
    details: dict[str, Any] = Field(default_factory=dict)


class PipelineRunReport(BaseModel):
    """Unified report from an orchestrated pipeline run."""

    repo_root: str
    outcomes: list[StageOutcome] = Field(default_factory=list)

    def add(self, outcome: StageOutcome) -> None:
        self.outcomes.append(outcome)
