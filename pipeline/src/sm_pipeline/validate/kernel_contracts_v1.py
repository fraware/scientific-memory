"""Kernel contract v1 validation gate (SPEC 8.x / kernel-contracts-v1)."""

from __future__ import annotations

import json
from pathlib import Path


class KernelContractV1Error(Exception):
    """Raised when tested kernels fail kernel-contract v1 completeness checks."""


def validate_kernel_contracts_v1(repo_root: Path) -> None:
    """
    Tested-kernel completeness checks.

    For each kernel with `test_status: "tested"` and non-empty `linked_theorem_cards`,
    require `contract_v1` and enforce:
    - non-empty units and domains (inputs/outputs)
    - numerically_witnessed witness_type
    - non-empty obligation expectations
    - satisfied obligations match `linked_theorem_cards`
    - unsatisfied obligations must be empty
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
        test_status = (k.get("test_status") or "").strip()
        linked = k.get("linked_theorem_cards") or []
        if test_status != "tested":
            continue
        if not isinstance(linked, list) or not linked:
            continue

        io_raw = k.get("io_typing")
        if not isinstance(io_raw, dict):
            raise KernelContractV1Error(
                f"Kernel {kid} is tested but missing io_typing (typed input/output bindings)."
            )
        ins = io_raw.get("inputs")
        outs = io_raw.get("outputs")
        if not isinstance(ins, list) or not isinstance(outs, list):
            raise KernelContractV1Error(f"Kernel {kid} io_typing.inputs/outputs must be arrays.")

        contract = k.get("contract_v1")
        if not isinstance(contract, dict):
            raise KernelContractV1Error(
                f"Kernel {kid} is tested but missing contract_v1; add structured "
                "kernel contract (units/domains/tolerances/witness/obligations)."
            )

        witness_type = contract.get("witness_type")
        if witness_type != "numerically_witnessed":
            raise KernelContractV1Error(
                f"Kernel {kid} has contract_v1.witness_type={witness_type!r}; "
                "must be 'numerically_witnessed' for now."
            )

        units = contract.get("units") or {}
        domains = contract.get("domains") or {}
        if not isinstance(units, dict) or not isinstance(domains, dict):
            raise KernelContractV1Error(f"Kernel {kid} contract_v1.units/domains must be objects.")

        u_inputs_raw = units.get("inputs")
        u_inputs = u_inputs_raw if isinstance(u_inputs_raw, dict) else {}
        u_outputs_raw = units.get("outputs")
        u_outputs = u_outputs_raw if isinstance(u_outputs_raw, dict) else {}
        d_inputs_raw = domains.get("inputs")
        d_inputs = d_inputs_raw if isinstance(d_inputs_raw, dict) else {}
        d_outputs_raw = domains.get("outputs")
        d_outputs = d_outputs_raw if isinstance(d_outputs_raw, dict) else {}

        if not u_inputs or not u_outputs:
            raise KernelContractV1Error(
                f"Kernel {kid} contract_v1.units.inputs/outputs must be non-empty."
            )
        in_names = {str(b.get("name")) for b in ins if isinstance(b, dict) and b.get("name")}
        out_names = {str(b.get("name")) for b in outs if isinstance(b, dict) and b.get("name")}
        if in_names != set(u_inputs.keys()) or out_names != set(u_outputs.keys()):
            raise KernelContractV1Error(
                f"Kernel {kid} io_typing names must match contract_v1.units input/output keys: "
                f"io inputs={sorted(in_names)} units inputs={sorted(u_inputs.keys())}; "
                f"io outputs={sorted(out_names)} units outputs={sorted(u_outputs.keys())}."
            )
        for b in ins:
            if not isinstance(b, dict):
                continue
            nk = (b.get("numeric_kind") or "").strip()
            nm = str(b.get("name") or "")
            dom_s = (d_inputs.get(nm) or "").lower()
            if nk == "nonnegative_float" and ">=" not in dom_s and "≥" not in dom_s:
                raise KernelContractV1Error(
                    f"Kernel {kid} io_typing input {nm!r} is nonnegative_float but "
                    f"contract_v1.domains.inputs[{nm!r}] lacks a nonnegativity hint (e.g. '>= 0')."
                )
            if nk == "positive_float" and ">" not in dom_s:
                raise KernelContractV1Error(
                    f"Kernel {kid} io_typing input {nm!r} is positive_float but "
                    f"contract_v1.domains.inputs[{nm!r}] lacks a positivity hint (e.g. '> 0')."
                )
        if not d_inputs or not d_outputs:
            raise KernelContractV1Error(
                f"Kernel {kid} contract_v1.domains.inputs/outputs must be non-empty."
            )

        obligations = contract.get("obligations") or {}
        if not isinstance(obligations, dict):
            raise KernelContractV1Error(f"Kernel {kid} contract_v1.obligations must be an object.")

        expected = obligations.get("expected_linked_theorem_cards") or []
        satisfied = obligations.get("satisfied_linked_theorem_cards") or []
        unsatisfied = obligations.get("unsatisfied_linked_theorem_cards") or []

        if not isinstance(expected, list) or not expected:
            raise KernelContractV1Error(
                "Kernel "
                f"{kid} contract_v1.obligations.expected_linked_theorem_cards "
                "must be non-empty."
            )
        if not isinstance(satisfied, list):
            raise KernelContractV1Error(
                "Kernel "
                f"{kid} contract_v1.obligations.satisfied_linked_theorem_cards "
                "must be a list."
            )
        if not isinstance(unsatisfied, list):
            raise KernelContractV1Error(
                "Kernel "
                f"{kid} contract_v1.obligations.unsatisfied_linked_theorem_cards "
                "must be a list."
            )

        expected_set = set(expected)
        satisfied_set = set(satisfied)
        linked_set = set(linked)

        if expected_set != linked_set:
            raise KernelContractV1Error(
                f"Kernel {kid} under-linkage: obligations.expected_linked_theorem_cards "
                f"={sorted(expected_set)} must match linked_theorem_cards={sorted(linked_set)}."
            )
        if satisfied_set != linked_set:
            raise KernelContractV1Error(
                f"Kernel {kid} contract mismatch: obligations.satisfied_linked_theorem_cards "
                f"={sorted(satisfied_set)} must match linked_theorem_cards={sorted(linked_set)}."
            )
        if unsatisfied:
            raise KernelContractV1Error(
                "Kernel "
                f"{kid} has unsatisfied obligations "
                "(contract_v1.obligations.unsatisfied_linked_theorem_cards)."
            )
