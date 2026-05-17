"""Validation via pcs-core (canonical PCS authority)."""

from __future__ import annotations

from typing import Any


def pcs_core_available() -> bool:
    try:
        import pcs_core.validate  # noqa: F401
    except ImportError:
        return False
    return True


def validate_with_pcs_core(bundle: dict[str, Any]) -> list[str]:
    """Run pcs-core schema + semantic validation."""
    if not pcs_core_available():
        return []

    from pcs_core.validate import ValidationError as PcsCoreValidationError
    from pcs_core.validate import detect_artifact_type, validate_artifact

    from sm_pipeline.pcs_import.bundle_utils import bundle_for_validation

    payload = bundle_for_validation(bundle)
    try:
        artifact_type = detect_artifact_type(payload) or "SignedScienceClaimBundle.v0"
        validate_artifact(payload, artifact_type)
    except PcsCoreValidationError as exc:
        return list(exc.errors or [str(exc)])
    return []
