#!/usr/bin/env python3
"""Reproducible Freundlich witness: k=2, c=1, n=2 -> amount=2."""

from adsorption_kernel.model import freundlich_amount

if __name__ == "__main__":
    amt = freundlich_amount(2.0, 1.0, 2.0)
    print(f"freundlich_amount(2,1,2)={amt}")
    assert abs(amt - 2.0) < 1e-9, "expected 2.0"
