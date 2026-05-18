"""Validate ArtifactRegistry.v0 (pcs-core consumer)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from sm_pipeline.pcs_validate.canonical_hash import canonical_hash
from sm_pipeline.pcs_validate.pcs_core_hook import pcs_core_available, validate_protocol_artifact
from sm_pipeline.pcs_validate.validator import BundleValidationError, validator_for

ARTIFACT_REGISTRY_SCHEMA = "ArtifactRegistry.v0.schema.json"


def _load_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as exc:
        raise BundleValidationError(f"Artifact registry JSON parse error: {exc}") from exc
    if not isinstance(data, dict):
        raise BundleValidationError("Artifact registry root must be a JSON object")
    return data


def validate_artifact_registry(
    path: Path,
    *,
    repo_root: Path | None = None,
) -> list[str]:
    path = path.resolve()
    if not path.is_file():
        return [f"missing artifact registry: {path}"]
    root = repo_root or Path(__file__).resolve().parents[4]
    try:
        data = _load_json(path)
    except BundleValidationError as exc:
        return [str(exc)]
    errors: list[str] = []
    if pcs_core_available():
        errors.extend(validate_protocol_artifact(data, "ArtifactRegistry.v0"))
    else:
        try:
            validator = validator_for(ARTIFACT_REGISTRY_SCHEMA, root)
        except FileNotFoundError as exc:
            return [str(exc)]
        for err in sorted(validator.iter_errors(data), key=lambda item: item.path):
            errors.append(err.message)
    expected_digest = data.get("signature_or_digest")
    if isinstance(expected_digest, str):
        actual = canonical_hash(data)
        if expected_digest != actual:
            errors.append(
                f"signature_or_digest mismatch (expected {expected_digest}, computed {actual})",
            )
    else:
        errors.append("signature_or_digest is required")
    return errors


def validate_artifact_registry_or_raise(path: Path, *, repo_root: Path | None = None) -> dict[str, Any]:
    errors = validate_artifact_registry(path, repo_root=repo_root)
    if errors:
        raise BundleValidationError("; ".join(errors))
    return _load_json(path.resolve())
