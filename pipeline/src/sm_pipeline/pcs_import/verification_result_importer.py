"""Import VerificationResult.v0 artifacts (embedded or sidecar)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from sm_pipeline.pcs_validate.validator import BundleValidationError, validator_for


def load_verification_result(path: Path, *, repo_root: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise BundleValidationError("VerificationResult must be a JSON object")
    validator = validator_for("verification_result.schema.json", repo_root)
    errors = [e.message for e in validator.iter_errors(data)]
    if errors:
        raise BundleValidationError("; ".join(errors))
    return data


def merge_verification_result(
    bundle: dict[str, Any],
    verification_result: dict[str, Any],
) -> dict[str, Any]:
    """Attach verification result without mutating nested artifact IDs."""
    merged = dict(bundle)
    merged["verification_result"] = verification_result
    scb = merged.get("science_claim_bundle")
    if isinstance(scb, dict) and scb.get("verification_result") is None:
        scb_copy = dict(scb)
        scb_copy["verification_result"] = verification_result
        merged["science_claim_bundle"] = scb_copy
    return merged
