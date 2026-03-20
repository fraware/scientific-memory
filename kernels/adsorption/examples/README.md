# Kernel witness examples (SPEC 8.6)

Reproducible numeric runs for adsorption kernels. Verification boundary: **numerically_witnessed** (tests + these scripts attest behavior; formal proofs live in Lean).

From repo root, with kernel env:

```bash
uv run --project kernels/adsorption python kernels/adsorption/examples/run_langmuir_demo.py
uv run --project kernels/adsorption python kernels/adsorption/examples/run_freundlich_demo.py
uv run --project kernels/adsorption python kernels/adsorption/examples/run_adsorption_sweep_demo.py
```

Expected output lines are documented in each script. CI does not run these by default; `pytest` in `kernels/adsorption/tests/` is the enforced witness suite.
