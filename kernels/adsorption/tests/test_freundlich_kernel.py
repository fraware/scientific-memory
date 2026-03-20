"""Witness tests for Freundlich kernel (numerically_witnessed)."""

import math

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from adsorption_kernel.model import freundlich_amount, run_freundlich
from adsorption_kernel.schema import FreundlichInput, FreundlichOutput

from kernel_conformance import assert_monotone_nondecreasing


def test_freundlich_at_one() -> None:
    """At c=1, amount = k * 1^(1/n) = k for n != 0."""
    assert math.isclose(freundlich_amount(2.0, 1.0, 2.0), 2.0)


def test_freundlich_nonneg_for_nonneg_k() -> None:
    """k >= 0, c > 0, n > 0 implies amount >= 0."""
    assert freundlich_amount(1.0, 0.5, 2.0) >= 0
    assert freundlich_amount(0.0, 1.0, 2.0) == 0.0


def test_freundlich_mono_in_c() -> None:
    """For k > 0, n > 0, larger c gives larger amount (smoke)."""
    k, n = 1.0, 2.0
    a1 = freundlich_amount(k, 0.25, n)
    a2 = freundlich_amount(k, 1.0, n)
    assert a2 > a1


def test_freundlich_monotone_in_c_grid() -> None:
    """Property-style check over a grid: c ↦ amount is nondecreasing."""
    k, n = 1.2, 2.5
    c_values = [0.05, 0.1, 0.25, 0.5, 1.0, 2.0, 4.0]
    vals = [freundlich_amount(k, c, n) for c in c_values]
    assert_monotone_nondecreasing(vals)


def test_freundlich_monotone_in_k_grid() -> None:
    """Property-style check over a grid: k ↦ amount is nondecreasing."""
    c, n = 1.6, 2.0
    k_values = [0.0, 0.25, 0.5, 1.0, 2.0, 4.0]
    vals = [freundlich_amount(k, c, n) for k in k_values]
    assert_monotone_nondecreasing(vals)


def test_freundlich_invalid_domain_nan() -> None:
    """c <= 0 or n == 0 yields nan."""
    assert math.isnan(freundlich_amount(1.0, 0.0, 2.0))
    assert math.isnan(freundlich_amount(1.0, -1.0, 2.0))
    assert math.isnan(freundlich_amount(1.0, 1.0, 0.0))


def test_run_freundlich_io() -> None:
    inp = FreundlichInput(k=1.0, c=1.0, n=2.0)
    out = run_freundlich(inp)
    assert isinstance(out, FreundlichOutput)
    assert math.isclose(out.amount, 1.0)


@pytest.mark.parametrize("k,c,n", [(1.0, 4.0, 2.0), (0.5, 8.0, 3.0)])
def test_freundlich_matches_manual(k: float, c: float, n: float) -> None:
    expected = k * (c ** (1.0 / n))
    assert math.isclose(freundlich_amount(k, c, n), expected)


@pytest.mark.parametrize("scale", [0.1, 0.5, 2.0, 5.0])
def test_freundlich_homogeneous_in_k(scale: float) -> None:
    """Property-style check: amount(a*k,c,n) == a*amount(k,c,n)."""
    k, c, n = 1.7, 2.4, 3.0
    lhs = freundlich_amount(scale * k, c, n)
    rhs = scale * freundlich_amount(k, c, n)
    assert math.isclose(lhs, rhs, rel_tol=1e-12, abs_tol=1e-12)


_pos_n = st.floats(min_value=0.2, max_value=8.0, allow_nan=False, allow_infinity=False)
_pos_c = st.floats(min_value=1e-4, max_value=20.0, allow_nan=False, allow_infinity=False)
_nonneg_k = st.floats(min_value=0.0, max_value=20.0, allow_nan=False, allow_infinity=False)


@settings(max_examples=35, deadline=None)
@given(k=_nonneg_k, c=_pos_c, n=_pos_n)
def test_freundlich_hypothesis_matches_formula(k: float, c: float, n: float) -> None:
    expected = k * (c ** (1.0 / n))
    assert math.isclose(freundlich_amount(k, c, n), expected, rel_tol=1e-12, abs_tol=1e-12)


@settings(max_examples=35, deadline=None)
@given(
    k=st.floats(min_value=1e-6, max_value=15.0, allow_nan=False, allow_infinity=False),
    c1=_pos_c,
    dc=st.floats(min_value=1e-4, max_value=5.0, allow_nan=False, allow_infinity=False),
    n=_pos_n,
)
def test_freundlich_hypothesis_monotone_in_c(k: float, c1: float, dc: float, n: float) -> None:
    c2 = c1 + dc
    a1 = freundlich_amount(k, c1, n)
    a2 = freundlich_amount(k, c2, n)
    assert a1 <= a2 + 1e-9


@settings(max_examples=35, deadline=None)
@given(
    c=_pos_c,
    n=_pos_n,
    k1=st.floats(min_value=0.0, max_value=10.0, allow_nan=False, allow_infinity=False),
    dk=st.floats(min_value=1e-6, max_value=10.0, allow_nan=False, allow_infinity=False),
)
def test_freundlich_hypothesis_monotone_in_k(c: float, n: float, k1: float, dk: float) -> None:
    k2 = k1 + dk
    assert freundlich_amount(k1, c, n) <= freundlich_amount(k2, c, n) + 1e-9


@settings(max_examples=30, deadline=None)
@given(
    scale=st.floats(min_value=1e-6, max_value=50.0, allow_nan=False, allow_infinity=False),
    k=st.floats(min_value=0.1, max_value=10.0, allow_nan=False, allow_infinity=False),
    c=_pos_c,
    n=_pos_n,
)
def test_freundlich_hypothesis_homogeneous_k(scale: float, k: float, c: float, n: float) -> None:
    lhs = freundlich_amount(scale * k, c, n)
    rhs = scale * freundlich_amount(k, c, n)
    assert math.isclose(lhs, rhs, rel_tol=1e-11, abs_tol=1e-11)
