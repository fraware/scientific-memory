"""Input/output schema for adsorption kernel."""

from pydantic import BaseModel


class LangmuirInput(BaseModel):
    K: float
    P: float


class LangmuirOutput(BaseModel):
    coverage: float


class FreundlichInput(BaseModel):
    """k, c, n for amount = k * c^(1/n). Typical use: c > 0, n != 0."""

    k: float
    c: float
    n: float


class FreundlichOutput(BaseModel):
    amount: float
