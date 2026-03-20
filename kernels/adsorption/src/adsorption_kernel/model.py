"""Langmuir and Freundlich isotherm models. Verification boundary: numerically_witnessed."""

import math

from adsorption_kernel.schema import (
    FreundlichInput,
    FreundlichOutput,
    LangmuirInput,
    LangmuirOutput,
)


def langmuir_coverage(K: float, P: float) -> float:
    """θ = (K*P) / (1 + K*P). Linked to theorem card langmuir_1918_adsorption_card_001."""
    if 1 + K * P == 0:
        return 0.0
    return (K * P) / (1 + K * P)


def run(input_data: LangmuirInput) -> LangmuirOutput:
    return LangmuirOutput(coverage=langmuir_coverage(input_data.K, input_data.P))


def freundlich_amount(k: float, c: float, n: float) -> float:
    """
    amount = k * c^(1/n). Linked to theorem card freundlich_1906_adsorption_card_001.
    Domain: c > 0, n != 0 (matches typical Freundlich use; undefined otherwise returns nan).
    """
    if c <= 0 or n == 0 or not math.isfinite(k) or not math.isfinite(c) or not math.isfinite(n):
        return float("nan")
    return k * (c ** (1.0 / n))


def run_freundlich(input_data: FreundlichInput) -> FreundlichOutput:
    return FreundlichOutput(amount=freundlich_amount(input_data.k, input_data.c, input_data.n))
