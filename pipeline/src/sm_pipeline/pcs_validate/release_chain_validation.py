"""Validate ReleaseChainValidationResult.v0 (pcs-core consumer)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from sm_pipeline.pcs_validate.canonical_hash import canonical_hash
from sm_pipeline.pcs_validate.pcs_core_hook import pcs_core_available, validate_protocol_artifact
from sm_pipeline.pcs_validate.placeholder_commits import validate_source_commit_for_release
from sm_pipeline.pcs_validate.validator import BundleValidationError, validator_for

RELEASE_CHAIN_VALIDATION_FILENAME = "ReleaseChainValidationResult.v0.json"
RELEASE_CHAIN_VALIDATION_SCHEMA = "ReleaseChainValidationResult.v0.schema.json"
PROOF_CHECKED_STATUS = "ProofChecked"


def _repo_root(repo_root: Path | None) -> Path:
    if repo_root is not None:
        return repo_root.resolve()
    return Path(__file__).resolve().parents[4]


def _load_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as exc:
        raise BundleValidationError(
            f"Release chain validation JSON parse error: {exc}",
        ) from exc
    if not isinstance(data, dict):
        raise BundleValidationError("Release chain validation root must be a JSON object")
    return data


def _validate_schema(data: dict[str, Any], repo_root: Path) -> list[str]:
    if pcs_core_available():
        return validate_protocol_artifact(data, "ReleaseChainValidationResult.v0")
    errors: list[str] = []
    try:
        validator = validator_for(RELEASE_CHAIN_VALIDATION_SCHEMA, repo_root)
    except FileNotFoundError as exc:
        return [str(exc)]
    for err in sorted(validator.iter_errors(data), key=lambda item: item.path):
        errors.append(err.message)
    return errors


def validate_release_chain_validation(
    validation_path: Path,
    *,
    repo_root: Path | None = None,
    expected_release_id: str | None = None,
) -> list[str]:
    path = validation_path.resolve()
    if not path.is_file():
        return [f"missing release chain validation: {path}"]

    root = _repo_root(repo_root)
    try:
        data = _load_json(path)
    except BundleValidationError as exc:
        return [str(exc)]

    errors: list[str] = []
    errors.extend(_validate_schema(data, root))

    commit = data.get("source_commit")
    if isinstance(commit, str):
        msg = validate_source_commit_for_release(commit, path="source_commit")
        if msg:
            errors.append(msg)

    expected_digest = data.get("signature_or_digest")
    if isinstance(expected_digest, str):
        actual = canonical_hash(data)
        if expected_digest != actual:
            errors.append(
                "signature_or_digest mismatch "
                f"(expected {expected_digest}, computed {actual})",
            )
    else:
        errors.append("signature_or_digest is required")

    status = data.get("status")
    if status != PROOF_CHECKED_STATUS:
        errors.append(
            f"release chain validation status must be {PROOF_CHECKED_STATUS} "
            f"(got {status!r})",
        )

    checks = data.get("checks")
    if isinstance(checks, list):
        for index, check in enumerate(checks):
            if isinstance(check, dict) and check.get("status") == "failed":
                check_id = check.get("check_id", index)
                errors.append(f"checks[{check_id}]: status failed")

    failure_codes = data.get("failure_codes")
    if isinstance(failure_codes, list) and failure_codes:
        errors.append(f"failure_codes must be empty when status is {PROOF_CHECKED_STATUS}")

    if expected_release_id is not None:
        release_id = data.get("release_id")
        if release_id != expected_release_id:
            errors.append(
                f"release_id mismatch (expected {expected_release_id}, got {release_id!r})",
            )

    return errors


def validate_release_chain_validation_or_raise(
    validation_path: Path,
    *,
    repo_root: Path | None = None,
    expected_release_id: str | None = None,
) -> dict[str, Any]:
    errors = validate_release_chain_validation(
        validation_path,
        repo_root=repo_root,
        expected_release_id=expected_release_id,
    )
    if errors:
        raise BundleValidationError("; ".join(errors))
    return _load_json(validation_path.resolve())


def resolve_release_chain_validation_path(release_dir: Path) -> Path:
    from sm_pipeline.pcs_validate.release_paths import resolve_release_chain_validation_path as _resolve

    return _resolve(release_dir)


def require_release_chain_validation(
    release_dir: Path,
    *,
    repo_root: Path | None = None,
    expected_release_id: str | None = None,
) -> dict[str, Any]:
    path = resolve_release_chain_validation_path(release_dir)
    return validate_release_chain_validation_or_raise(
        path,
        repo_root=repo_root,
        expected_release_id=expected_release_id,
    )
