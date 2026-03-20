from pydantic import BaseModel, Field
from typing import Literal


class ExecutableKernel(BaseModel):
    id: str
    domain: str
    input_schema: str
    output_schema: str
    semantic_contract: str
    unit_constraints: list[str] = Field(default_factory=list)
    linked_theorem_cards: list[str]
    test_status: Literal["untested", "tested", "failing"] | None = None
