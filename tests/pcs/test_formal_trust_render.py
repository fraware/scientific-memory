"""Formal Trust Kernel read-model and portal view contracts."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from sm_pipeline.pcs_import.formal_trust_protocol import (
    FORMAL_NON_CLAIMS,
    MILESTONE_THEOREMS,
    build_formal_trust_kernel_view,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURES = Path(__file__).resolve().parent / "fixtures"
CANONICAL = FIXTURES / "canonical_pcs_read_model.json"
LABTRUST_PHASE2 = FIXTURES / "labtrust-release" / ".phase2-read-model.json"


def _supplemental_from_docs(
    *,
    obligation_status: str = "ProofChecked",
    lean_status: str = "ProofChecked",
    first_result: str = "passed",
) -> list[dict]:
    """Minimal supplemental rows for unit tests (no release dir)."""
    obligation_payload = {
        "schema_version": "v0",
        "obligation_set_id": "obl-set-test",
        "release_id": "release-test",
        "obligations": [
            {
                "obligation_id": spec["obligation_id"],
                "predicate": spec["predicate"],
                "lean_theorem": spec["lean_theorem"],
                "trust_boundary_invariant": spec["trust_boundary_invariant"],
                "formal_scope": "test scope",
                "source_artifacts": list(spec["source_artifacts"]),
            }
            for spec in MILESTONE_THEOREMS[:2]
        ],
    }
    lean_payload = {
        "schema_version": "v0",
        "check_result_id": "lean-check-test",
        "release_id": "release-test",
        "obligation_set_id": "obl-set-test",
        "status": lean_status,
        "lean_version": "leanprover/lean4:v4.24.0",
        "checked_at": "2026-05-19T00:00:00Z",
        "checker": "pcs-core",
        "results": [
            {
                "obligation_id": MILESTONE_THEOREMS[0]["obligation_id"],
                "lean_theorem": MILESTONE_THEOREMS[0]["lean_theorem"],
                "status": obligation_status,
                "source_artifacts": list(MILESTONE_THEOREMS[0]["source_artifacts"]),
                "result": first_result,
                "checked_at": "2026-05-19T00:00:00Z",
                "lean_version": "leanprover/lean4:v4.24.0",
                "expected": "sha256:expected",
                "actual": "sha256:actual",
                "responsible_component": "LabTrust-Gym",
                "repair_hint": "Align trace_certificate trace_hash with runtime_receipt.",
                "pf_explain": "bundle_hash mismatch in verified_input",
            },
            {
                "obligation_id": MILESTONE_THEOREMS[1]["obligation_id"],
                "lean_theorem": MILESTONE_THEOREMS[1]["lean_theorem"],
                "status": "ProofChecked",
                "source_artifacts": list(MILESTONE_THEOREMS[1]["source_artifacts"]),
                "result": "passed",
                "checked_at": "2026-05-19T00:00:00Z",
                "lean_version": "leanprover/lean4:v4.24.0",
            },
        ],
        "pf_explain": "release-level explain output",
    }
    return [
        {
            "name": "proof_obligation.v0.json",
            "artifact_type": "ProofObligation.v0",
            "payload": obligation_payload,
        },
        {
            "name": "lean_check_result.v0.json",
            "artifact_type": "LeanCheckResult.v0",
            "payload": lean_payload,
        },
    ]


def test_build_formal_trust_kernel_view_surfaces_failed_check_fields() -> None:
    kernel = build_formal_trust_kernel_view(_supplemental_from_docs(first_result="failed"))
    assert kernel is not None
    failed = [
        row
        for row in kernel.get("lean_check_results") or []
        if row.get("result") == "failed"
    ]
    assert len(failed) == 1
    row = failed[0]
    assert row.get("lean_theorem") == "PCS.CertificateMatchesRuntime"
    assert row.get("expected") == "sha256:expected"
    assert row.get("actual") == "sha256:actual"
    assert row.get("responsible_component") == "LabTrust-Gym"
    assert row.get("repair_hint")
    assert row.get("pf_explain")


def test_build_formal_trust_kernel_view_includes_required_non_claims() -> None:
    kernel = build_formal_trust_kernel_view(
        _supplemental_from_docs(first_result="passed"),
    )
    assert kernel is not None
    assert kernel.get("formal_non_claims") == list(FORMAL_NON_CLAIMS)
    assert kernel.get("overall_status") == "ProofChecked"


def test_canonical_read_model_has_formal_trust_kernel() -> None:
    assert CANONICAL.is_file()
    read_model = json.loads(CANONICAL.read_text(encoding="utf-8"))
    kernel = read_model.get("formal_trust_kernel")
    assert isinstance(kernel, dict)
    assert kernel.get("title") == "Formal Trust Kernel"
    assert len(kernel.get("lean_check_results") or []) == len(MILESTONE_THEOREMS)
    assert kernel.get("formal_non_claims") == list(FORMAL_NON_CLAIMS)


def test_labtrust_phase2_fixture_passes_formal_trust_portal_contract() -> None:
    import subprocess

    script = REPO_ROOT / "portal" / "scripts" / "verify-pcs-phase2-read-model.mjs"
    if not LABTRUST_PHASE2.is_file():
        pytest.skip("run: just refresh-pcs-release")

    result = subprocess.run(
        ["node", str(script), str(LABTRUST_PHASE2)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
