from pydantic import BaseModel, Field
from typing import Literal


class SourceInfo(BaseModel):
    kind: Literal["pdf", "latex", "arxiv_bundle", "other"]
    path: str
    sha256: str
    doi: str | None = None
    arxiv_id: str | None = None


class Paper(BaseModel):
    id: str
    title: str
    authors: list[str]
    year: int
    domain: Literal[
        "chemistry",
        "mathematics",
        "physics",
        "probability",
        "control",
        "quantum_information",
        "other",
    ]
    abstract: str | None = None
    tags: list[str] = Field(default_factory=list)
    source: SourceInfo
    artifact_status: Literal["admitted", "in_progress", "published", "archived"]
    ingestion_status: Literal["pending", "ingested", "failed"] | None = None
    first_artifact_at: str | None = None
