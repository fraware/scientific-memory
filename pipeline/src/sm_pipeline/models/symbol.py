from pydantic import BaseModel, Field
from typing import Any


class DimensionalMetadata(BaseModel):
    kind: str | None = None
    unit: str | None = None
    dimension: str | None = None


class Symbol(BaseModel):
    id: str
    paper_id: str
    raw_latex: str
    normalized_name: str
    type_hint: str | None = None
    dimensional_metadata: dict[str, Any] | None = None
    ambiguity_flags: list[str] = Field(default_factory=list)
