from pydantic import BaseModel, Field
from typing import Literal


class IoBinding(BaseModel):
    name: str
    numeric_kind: Literal["float", "int", "nonnegative_float", "positive_float"]


class KernelIoTyping(BaseModel):
    inputs: list[IoBinding]
    outputs: list[IoBinding]


class KernelContractV1Units(BaseModel):
    inputs: dict[str, str]
    outputs: dict[str, str]


class KernelContractV1Domains(BaseModel):
    inputs: dict[str, str]
    outputs: dict[str, str]


class KernelContractV1Tolerances(BaseModel):
    absolute_error: float
    relative_error: float


class KernelContractV1Obligations(BaseModel):
    expected_linked_theorem_cards: list[str]
    satisfied_linked_theorem_cards: list[str]
    unsatisfied_linked_theorem_cards: list[str]


class KernelContractV1(BaseModel):
    units: KernelContractV1Units
    domains: KernelContractV1Domains
    exceptional_cases: list[str] = Field(default_factory=list)
    approximation_regimes: list[str] = Field(default_factory=list)
    tolerances: KernelContractV1Tolerances
    witness_type: Literal["numerically_witnessed"]
    obligations: KernelContractV1Obligations


class ExecutableKernel(BaseModel):
    id: str
    domain: str
    io_typing: KernelIoTyping
    input_schema: str | None = None
    output_schema: str | None = None
    semantic_contract: str
    unit_constraints: list[str] = Field(default_factory=list)
    linked_theorem_cards: list[str]
    test_status: Literal["untested", "tested", "failing"] | None = None
    contract_v1: KernelContractV1 | None = None
