"""Detect LabTrust legacy vs pcs-core signed bundle shapes."""

from __future__ import annotations

from typing import Any


def get_science_claim_bundle(bundle: dict[str, Any]) -> dict[str, Any] | None:
    scb = bundle.get("science_claim_bundle")
    return scb if isinstance(scb, dict) else None


def is_legacy_signed_bundle(bundle: dict[str, Any]) -> bool:
    """
    Portal/LabTrust envelope: nested ScienceClaimBundle.v0 with claim, runtime_receipt,
    trace_certificate (singular).
    """
    scb = get_science_claim_bundle(bundle)
    if scb is None:
        return False
    if scb.get("schema_version") == "ScienceClaimBundle.v0":
        return True
    if "claim" in scb and "claim_artifact" not in scb:
        return True
    return False


def is_pcs_core_signed_bundle(bundle: dict[str, Any]) -> bool:
    """Provability Fabric / pcs-core SignedScienceClaimBundle.v0 envelope."""
    if bundle.get("signed_bundle_id") and get_science_claim_bundle(bundle):
        return True
    if bundle.get("signer") and bundle.get("signed_at") and get_science_claim_bundle(bundle):
        return True
    scb = get_science_claim_bundle(bundle)
    if isinstance(scb, dict) and scb.get("schema_version") == "v0" and "claim_artifact" in scb:
        return True
    return False
