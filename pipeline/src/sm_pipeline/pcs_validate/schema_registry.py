"""Resolve pcs-core canonical schema file names (Scientific Memory consumes, does not own)."""

from __future__ import annotations

from pathlib import Path

# Canonical pcs-core v0.1 schema filenames (see SentinelOps-CI/pcs-core).
SIGNED_BUNDLE_SCHEMA = "SignedScienceClaimBundle.v0.schema.json"
SCIENCE_CLAIM_BUNDLE_SCHEMA = "ScienceClaimBundle.v0.schema.json"
VERIFICATION_RESULT_SCHEMA = "VerificationResult.v0.schema.json"

LEGACY_SIGNED_BUNDLE_SCHEMA = "legacy/LabTrust.SignedScienceClaimBundle.v0.schema.json"
LEGACY_SCIENCE_CLAIM_BUNDLE_SCHEMA = "legacy/LabTrust.ScienceClaimBundle.v0.schema.json"
LEGACY_VERIFICATION_RESULT_SCHEMA = "legacy/LabTrust.VerificationResult.v0.schema.json"

# Legacy aliases kept for compatibility; new code and docs must use canonical names.
SCHEMA_ALIASES: dict[str, str] = {
    "signed_science_claim_bundle.schema.json": SIGNED_BUNDLE_SCHEMA,
    "science_claim_bundle.schema.json": SCIENCE_CLAIM_BUNDLE_SCHEMA,
    "verification_result.schema.json": VERIFICATION_RESULT_SCHEMA,
}


def resolve_schema_path(schemas_dir: Path, name: str) -> Path:
    """Return path to schema file, resolving legacy alias to canonical filename."""
    canonical = SCHEMA_ALIASES.get(name, name)
    path = schemas_dir / canonical
    if path.is_file():
        return path
    # Fallback: requested name as-is (e.g. artifact_base).
    fallback = schemas_dir / name
    if fallback.is_file():
        return fallback
    raise FileNotFoundError(f"PCS schema not found: {name} (resolved {canonical})")
