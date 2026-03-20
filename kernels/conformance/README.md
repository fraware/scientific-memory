# kernel-conformance

Domain-agnostic test helpers for executable kernels in Scientific Memory (numeric closeness, monotonicity grids, etc.).

Kernel packages (for example `kernels/adsorption`) should depend on this workspace package and import `kernel_conformance` in tests instead of duplicating helpers.

## Usage

```python
from kernel_conformance import assert_close, assert_monotone_nondecreasing
```

## Adding a new kernel family

1. Add a new directory under `kernels/<family>/` with its own `pyproject.toml`.
2. Add `kernel-conformance` as a workspace dependency (see `kernels/adsorption/pyproject.toml`).
3. Reuse helpers here; add new shared helpers only when at least two families need them.
