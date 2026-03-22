"""Pydantic models for LLM proposal bundles (suggest-only; human-gated apply)."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator

from sm_pipeline.models.claim import Claim


class LlmRunMetadata(BaseModel):
    provider: str | None = None
    model: str | None = None
    model_version: str | None = None
    created_at: str | None = None
    latency_seconds: float | None = None
    temperature: float | None = None
    top_p: float | None = None
    max_tokens: int | None = None
    seed: int | None = None
    prompt_template_id: str | None = None
    prompt_template_sha256: str | None = None
    input_artifact_sha256: dict[str, str] | None = None
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    total_tokens: int | None = None
    estimated_cost_usd: float | None = None
    reviewer_time_seconds: float | None = Field(default=None, ge=0.0)
    reviewer_decision: Literal["pending", "accepted", "rejected", "edited"] | None = None
    promotion_outcome: str | None = None
    notes: str | None = None


class LlmClaimProposalEntry(BaseModel):
    claim: Claim
    rationale: str | None = None
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    evidence_quote: str | None = None


class LlmClaimProposalsBundle(BaseModel):
    paper_id: str
    schema_version: Literal["0.1.0"] = "0.1.0"
    verification_boundary: Literal["human_review_only"] = "human_review_only"
    metadata: LlmRunMetadata | None = None
    proposals: list[LlmClaimProposalEntry] = Field(default_factory=list)


class LlmMappingProposalEntry(BaseModel):
    claim_id: str
    lean_declaration_short_name: str
    rationale: str | None = None
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)


class LlmMappingProposalsBundle(BaseModel):
    paper_id: str
    schema_version: Literal["0.1.0"] = "0.1.0"
    verification_boundary: Literal["human_review_only"] = "human_review_only"
    metadata: LlmRunMetadata | None = None
    proposals: list[LlmMappingProposalEntry] = Field(default_factory=list)


class LlmLeanReplacement(BaseModel):
    find: str = Field(min_length=1)
    replace: str = ""


class LlmLeanProposalEntry(BaseModel):
    proposal_id: str = Field(min_length=1)
    paper_id: str
    claim_id: str | None = None
    target_file: str = Field(min_length=1)
    target_decl: str | None = None
    edit_kind: Literal["new_theorem", "proof_repair", "lemma_extraction"]
    replacements: list[LlmLeanReplacement] = Field(default_factory=list)
    patch_text: str | None = None
    rationale: str | None = None
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    safety_flags: list[str] = Field(default_factory=list)

    @field_validator("target_file")
    @classmethod
    def target_under_formal(cls, v: str) -> str:
        s = (v or "").strip().replace("\\", "/")
        if not s.startswith("formal/") or ".." in s:
            raise ValueError("target_file must be a repo-relative path under formal/ with no '..'")
        return s


class LlmLeanProposalsBundle(BaseModel):
    paper_id: str
    schema_version: Literal["0.1.0"] = "0.1.0"
    verification_boundary: Literal["human_review_only"] = "human_review_only"
    metadata: LlmRunMetadata | None = None
    proposals: list[LlmLeanProposalEntry] = Field(default_factory=list)
