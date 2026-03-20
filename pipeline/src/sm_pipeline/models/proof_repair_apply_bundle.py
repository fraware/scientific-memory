"""Pydantic models for proof_repair_apply_bundle.schema.json (human-gated Lean patches)."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class ProofRepairReplacement(BaseModel):
    find: str = Field(min_length=1)
    replace: str = ""


class ProofRepairPatch(BaseModel):
    relative_path: str
    replacements: list[ProofRepairReplacement] = Field(min_length=1)


class ProofRepairApplyBundle(BaseModel):
    verification_boundary: Literal["human_review_only"]
    review_record_path: str | None = None
    patches: list[ProofRepairPatch] = Field(min_length=1)
