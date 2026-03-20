#!/usr/bin/env python3
"""Reproducible Langmuir witness: K=1, P=1 -> coverage=0.5."""

from adsorption_kernel.model import langmuir_coverage

if __name__ == "__main__":
    theta = langmuir_coverage(1.0, 1.0)
    print(f"langmuir_coverage(1,1)={theta}")
    assert abs(theta - 0.5) < 1e-9, "expected 0.5"
