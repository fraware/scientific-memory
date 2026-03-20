import math

from hypothesis import given, settings
from hypothesis import strategies as st

from adsorption_kernel.model import langmuir_coverage, run
from adsorption_kernel.schema import LangmuirInput, LangmuirOutput

from kernel_conformance import assert_monotone_nondecreasing


def test_langmuir_coverage_bounds_on_grid() -> None:
    """Property-style check: for K >= 0, P >= 0 we stay in [0, 1)."""
    k_values = [0.0, 0.01, 0.1, 1.0, 10.0]
    p_values = [0.0, 0.05, 0.5, 1.0, 5.0]
    for k in k_values:
        for p in p_values:
            theta = langmuir_coverage(k, p)
            assert 0.0 <= theta <= 1.0


def test_run_io() -> None:
    inp = LangmuirInput(K=1.0, P=1.0)
    out = run(inp)
    assert isinstance(out, LangmuirOutput)
    assert 0 <= out.coverage <= 1


def test_langmuir_monotone_in_pressure() -> None:
    """Property-style check: fixed K > 0, theta increases with pressure."""
    k = 1.3
    p_values = [0.0, 0.1, 0.25, 0.5, 1.0, 2.0]
    values = [langmuir_coverage(k, p) for p in p_values]
    assert_monotone_nondecreasing(values)


def test_langmuir_monotone_in_k() -> None:
    """Property-style check: fixed P > 0, theta increases with K."""
    p = 0.8
    k_values = [0.0, 0.1, 0.25, 0.5, 1.0, 3.0]
    values = [langmuir_coverage(k, p) for k in k_values]
    assert_monotone_nondecreasing(values)


def test_langmuir_depends_on_product_kp() -> None:
    """Invariant: same K*P gives same coverage."""
    a = langmuir_coverage(2.0, 0.5)  # K*P = 1
    b = langmuir_coverage(4.0, 0.25)  # K*P = 1
    c = langmuir_coverage(0.5, 2.0)  # K*P = 1
    assert abs(a - b) < 1e-12
    assert abs(b - c) < 1e-12


@settings(max_examples=40, deadline=None)
@given(
    k=st.floats(min_value=0.0, max_value=1e3, allow_nan=False, allow_infinity=False),
    p=st.floats(min_value=0.0, max_value=1e3, allow_nan=False, allow_infinity=False),
)
def test_langmuir_hypothesis_bounds(k: float, p: float) -> None:
    theta = langmuir_coverage(k, p)
    assert 0.0 <= theta <= 1.0
    assert math.isfinite(theta)


@settings(max_examples=40, deadline=None)
@given(
    k=st.floats(min_value=1e-9, max_value=50.0, allow_nan=False, allow_infinity=False),
    p1=st.floats(min_value=0.0, max_value=25.0, allow_nan=False, allow_infinity=False),
    dp=st.floats(min_value=1e-9, max_value=25.0, allow_nan=False, allow_infinity=False),
)
def test_langmuir_hypothesis_monotone_pressure(k: float, p1: float, dp: float) -> None:
    p2 = p1 + dp
    t1 = langmuir_coverage(k, p1)
    t2 = langmuir_coverage(k, p2)
    assert t1 <= t2 + 1e-12


@settings(max_examples=40, deadline=None)
@given(
    p=st.floats(min_value=1e-9, max_value=50.0, allow_nan=False, allow_infinity=False),
    k1=st.floats(min_value=0.0, max_value=25.0, allow_nan=False, allow_infinity=False),
    dk=st.floats(min_value=1e-9, max_value=25.0, allow_nan=False, allow_infinity=False),
)
def test_langmuir_hypothesis_monotone_k(p: float, k1: float, dk: float) -> None:
    k2 = k1 + dk
    t1 = langmuir_coverage(k1, p)
    t2 = langmuir_coverage(k2, p)
    assert t1 <= t2 + 1e-12


@settings(max_examples=30, deadline=None)
@given(
    kp=st.floats(min_value=1e-6, max_value=80.0, allow_nan=False, allow_infinity=False),
)
def test_langmuir_hypothesis_invariant_kp(kp: float) -> None:
    a = langmuir_coverage(2.0, kp / 2.0)
    b = langmuir_coverage(1.0, kp)
    assert math.isclose(a, b, rel_tol=1e-9, abs_tol=1e-9)
