"""Kernel witness policy: linked kernels must declare test_status tested (SPEC v0.2)."""

import json
from pathlib import Path


class KernelWitnessError(Exception):
    pass


def validate_kernel_witness_policy(repo_root: Path) -> None:
    """
    Every kernel with non-empty linked_theorem_cards must have test_status 'tested'.
    Enforced witness suite: kernels/adsorption pytest in CI.
    """
    path = Path(repo_root).resolve() / "corpus" / "kernels.json"
    if not path.exists():
        return
    raw = path.read_text(encoding="utf-8").strip()
    if not raw:
        return
    kernels = json.loads(raw)
    if not isinstance(kernels, list):
        return
    for k in kernels:
        if not isinstance(k, dict):
            continue
        kid = k.get("id", "?")
        linked = k.get("linked_theorem_cards") or []
        if not linked:
            continue
        status = (k.get("test_status") or "").strip()
        if status != "tested":
            raise KernelWitnessError(
                f"Kernel {kid} links theorem cards but test_status is '{status or 'missing'}'; "
                "must be 'tested' with passing witness tests (kernels/adsorption pytest)."
            )
