"""Shared numeric conformance helpers for executable kernel witness tests (domain-agnostic)."""

from __future__ import annotations

import math
from collections.abc import Callable, Sequence


def assert_close(a: float, b: float, *, rel_tol: float = 1e-9, abs_tol: float = 1e-12) -> None:
    if not math.isclose(a, b, rel_tol=rel_tol, abs_tol=abs_tol):
        raise AssertionError(f"expected close values: {a!r} vs {b!r}")


def assert_monotone_nondecreasing(
    values: Sequence[float],
    *,
    tol: float = 1e-9,
) -> None:
    """Assert each value <= next (+ tol)."""
    for i in range(len(values) - 1):
        if values[i] > values[i + 1] + tol:
            raise AssertionError(f"not monotone at {i}: {values[i]!r} > {values[i + 1]!r}")


def assert_grid_monotone_in_first_arg(
    f: Callable[[float, float], float],
    xs: Sequence[float],
    y: float,
) -> None:
    """Property helper: f(x, y) nondecreasing in x for fixed y (grid smoke)."""
    vals = [f(x, y) for x in xs]
    assert_monotone_nondecreasing(vals)


__all__ = [
    "assert_close",
    "assert_grid_monotone_in_first_arg",
    "assert_monotone_nondecreasing",
]
