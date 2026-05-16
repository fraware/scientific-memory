"""Optional validation via pcs-core (canonical PCS protocol)."""

from __future__ import annotations

from typing import Any


def is_pcs_core_science_claim_bundle(scb: dict[str, Any]) -> bool:
    if scb.get("schema_version") == "v0":
        return True
    return "claim_artifact" in scb


def is_pcs_core_verification_result(vr: dict[str, Any]) -> bool:
    return "verification_id" in vr and "verifier" in vr


def validate_with_pcs_core(bundle: dict[str, Any]) -> list[str]:
    """Run pcs-core schema + semantic validation when the package is installed."""
    try:
        from pcs_core.validate import ValidationError as PcsCoreValidationError
        from pcs_core.validate import validate_artifact
    except ImportError:
        return []

    errors: list[str] = []
    scb = bundle.get("science_claim_bundle")
    if isinstance(scb, dict) and is_pcs_core_science_claim_bundle(scb):
        try:
            validate_artifact(scb, "ScienceClaimBundle.v0")
        except PcsCoreValidationError as exc:
            errors.extend(exc.errors or [str(exc)])

    vr = bundle.get("verification_result")
    if vr is None and isinstance(scb, dict):
        vr = scb.get("verification_result")
    if isinstance(vr, dict) and is_pcs_core_verification_result(vr):
        try:
            validate_artifact(vr, "VerificationResult.v0")
        except PcsCoreValidationError as exc:
            errors.extend(exc.errors or [str(exc)])

    return errors
