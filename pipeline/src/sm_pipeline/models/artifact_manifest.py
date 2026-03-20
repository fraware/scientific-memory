from pydantic import BaseModel, Field


class CoverageMetrics(BaseModel):
    claim_count: int
    mapped_claim_count: int
    machine_checked_count: int
    kernel_linked_count: int


class DependencyEdge(BaseModel):
    from_id: str = Field(alias="from")
    to: str

    class Config:
        populate_by_name = True


class ArtifactManifest(BaseModel):
    paper_id: str
    version: str
    build_hash: str
    build_hash_version: str | None = None
    coverage_metrics: CoverageMetrics
    generated_pages: list[str]
    declaration_index: list[str] = Field(default_factory=list)
    dependency_graph: list[dict[str, str]] = Field(default_factory=list)
    kernel_index: list[str] = Field(default_factory=list)
