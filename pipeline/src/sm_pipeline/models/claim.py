from pydantic import BaseModel, Field
from typing import Literal

from sm_pipeline.models.common import SourceSpan


class Claim(BaseModel):
    id: str
    paper_id: str
    section: str
    source_span: SourceSpan
    informal_text: str
    claim_type: Literal[
        "definition",
        "theorem",
        "lemma",
        "proposition",
        "corollary",
        "estimator",
        "identity",
        "conservation_law",
        "control_rule",
        "dimensional_constraint",
        "algorithmic_step",
        "acceptance_criterion",
        "editorial_exposition",
    ]
    mathematical_density: Literal["low", "medium", "high"] | None = None
    status: str
    linked_symbols: list[str] = Field(default_factory=list)
    linked_assumptions: list[str] = Field(default_factory=list)
    linked_formal_targets: list[str] = Field(default_factory=list)
    review_notes: str | None = None
