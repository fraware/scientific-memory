from pydantic import BaseModel
from typing import Literal

from sm_pipeline.models.common import SourceSpan


class Assumption(BaseModel):
    id: str
    paper_id: str
    source_span: SourceSpan
    text: str
    kind: Literal[
        "physical_regime",
        "domain_restriction",
        "smoothness",
        "boundedness",
        "measurement_assumption",
        "unit_convention",
        "approximation",
        "editorial",
        "other",
    ]
    explicit_or_implicit: Literal["explicit", "implicit"] | None = None
    normalization_status: Literal["raw", "normalized", "disputed"] | None = None
