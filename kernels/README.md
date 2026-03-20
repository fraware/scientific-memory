# Kernels

Executable kernels with declared verification boundaries and linked theorem cards. Each kernel has an input/output schema, optional `unit_constraints` (strings), and documents which formal declarations it implements. The portal renders kernel pages from `corpus/kernels.json` and linked theorem cards. See [Contributor playbook – Verification boundary](../docs/contributor-playbook.md#verification-boundary).

## Shared test helpers (`kernel-conformance`)

Cross-family numeric helpers (for example `assert_close`, monotonicity grids) live in the workspace package [`kernels/conformance/`](conformance/). New kernel families should depend on it in tests rather than copying helpers.

## Numeric witness contract (SPEC v0.2, numerically_witnessed)

Kernels that implement empirical or computational isotherms use boundary **numerically_witnessed**: correctness is attested by:

1. **Pytest suite** in `kernels/adsorption/tests/` — bounds plus property-style checks (monotonicity, invariants, scaling), and I/O schema validation. CI runs `uv run --project kernels/adsorption pytest` (see [JUSTFILE](../JUSTFILE) `just test`).
2. **Reproducible examples** in [kernels/adsorption/examples/](adsorption/examples/) — scripts with fixed inputs and small sweeps to validate behavior across ranges.

Formal proofs for related claims live under `formal/ScientificMemory/`; the kernel is a separate numeric witness, not a substitute for machine-checked Lean.

## Corpus enforcement

Pipeline validation requires every kernel with non-empty `linked_theorem_cards` to have `test_status: "tested"` (fail-fast). Kernels marked `tested` must keep passing the adsorption package pytest suite in CI.
