from pydantic import BaseModel, Field
from typing import Literal


class TheoremCard(BaseModel):
    id: str
    claim_id: str
    lean_decl: str
    file_path: str
    proof_status: str
    verification_boundary: Literal[
        "fully_machine_checked",
        "machine_checked_plus_axioms",
        "numerically_witnessed",
        "schema_valid_only",
        "human_review_only",
    ]
    dependency_ids: list[str] = Field(default_factory=list)
    dependency_extraction_method: str | None = None
    reviewer_status: Literal["unreviewed", "reviewed", "blocked", "accepted"]
    executable_links: list[str] = Field(default_factory=list)
    notes: str | None = None
