"""Validate ReleaseManifest.v0 against pcs-core protocol (consumer enforcement)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from sm_pipeline.pcs_validate.canonical_hash import canonical_hash, file_sha256_digest
from sm_pipeline.pcs_validate.pcs_core_hook import pcs_core_available, validate_protocol_artifact
from sm_pipeline.pcs_validate.placeholder_commits import validate_source_commit_for_release
from sm_pipeline.pcs_validate.validator import BundleValidationError, validator_for

SIGNED_BUNDLE_FILENAME = "signed_science_claim_bundle.json"
RELEASE_MANIFEST_SCHEMA = "ReleaseManifest.v0.schema.json"


def _repo_root(repo_root: Path | None) -> Path:
    if repo_root is not None:
        return repo_root.resolve()
    return Path(__file__).resolve().parents[4]


def _load_manifest(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as exc:
        raise BundleValidationError(f"Release manifest JSON parse error: {exc}") from exc
    if not isinstance(data, dict):
        raise BundleValidationError("Release manifest root must be a JSON object")
    return data


def _validate_schema(manifest: dict[str, Any], repo_root: Path) -> list[str]:
    if pcs_core_available():
        return validate_protocol_artifact(manifest, "ReleaseManifest.v0")
    errors: list[str] = []
    try:
        validator = validator_for(RELEASE_MANIFEST_SCHEMA, repo_root)
    except FileNotFoundError as exc:
        return [str(exc)]
    for err in sorted(validator.iter_errors(manifest), key=lambda item: item.path):
        errors.append(err.message)
    return errors


def _validate_provenance(manifest: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    producer_repos = manifest.get("producer_repos")
    if isinstance(producer_repos, dict):
        for name, pin in producer_repos.items():
            if not isinstance(pin, dict):
                continue
            commit = pin.get("commit")
            if isinstance(commit, str):
                msg = validate_source_commit_for_release(
                    commit,
                    path=f"producer_repos.{name}.commit",
                )
                if msg:
                    errors.append(msg)
    artifacts = manifest.get("artifacts")
    if isinstance(artifacts, dict):
        for name, entry in artifacts.items():
            if not isinstance(entry, dict):
                continue
            commit = entry.get("source_commit")
            if isinstance(commit, str):
                msg = validate_source_commit_for_release(
                    commit,
                    path=f"artifacts.{name}.source_commit",
                )
                if msg:
                    errors.append(msg)
    return errors


def _validate_artifact_hashes(manifest: dict[str, Any], base: Path) -> list[str]:
    errors: list[str] = []
    artifacts = manifest.get("artifacts")
    if not isinstance(artifacts, dict):
        return ["artifacts must be an object"]
    if SIGNED_BUNDLE_FILENAME not in artifacts:
        errors.append(f"artifacts must include {SIGNED_BUNDLE_FILENAME}")
    for name, entry in artifacts.items():
        if not isinstance(entry, dict):
            errors.append(f"artifacts.{name}: entry must be an object")
            continue
        expected = entry.get("sha256")
        if not isinstance(expected, str) or not expected.startswith("sha256:"):
            errors.append(f"artifacts.{name}: sha256 digest required")
            continue
        path = base / name
        if not path.is_file():
            errors.append(f"missing manifest artifact file {name}")
            continue
        actual = file_sha256_digest(path)
        if actual != expected:
            errors.append(
                f"artifacts.{name}: manifest digest mismatch (expected {expected}, got {actual})",
            )
    return errors


def validate_release_manifest(
    manifest_path: Path,
    *,
    repo_root: Path | None = None,
) -> list[str]:
    """Return validation errors for a ReleaseManifest.v0 on disk (empty when valid)."""
    path = manifest_path.resolve()
    if not path.is_file():
        return [f"missing release manifest: {path}"]

    root = _repo_root(repo_root)
    try:
        manifest = _load_manifest(path)
    except BundleValidationError as exc:
        return [str(exc)]

    errors: list[str] = []
    errors.extend(_validate_schema(manifest, root))
    errors.extend(_validate_provenance(manifest))

    expected_digest = manifest.get("signature_or_digest")
    if isinstance(expected_digest, str):
        actual_digest = canonical_hash(manifest)
        if expected_digest != actual_digest:
            errors.append(
                "signature_or_digest mismatch "
                f"(expected {expected_digest}, computed {actual_digest})",
            )
    else:
        errors.append("signature_or_digest is required")

    status = manifest.get("release_status")
    if status != "Validated":
        errors.append(f"release_status must be Validated for import (got {status!r})")

    errors.extend(_validate_artifact_hashes(manifest, path.parent))
    return errors


def validate_release_manifest_or_raise(
    manifest_path: Path,
    *,
    repo_root: Path | None = None,
) -> dict[str, Any]:
    errors = validate_release_manifest(manifest_path, repo_root=repo_root)
    if errors:
        raise BundleValidationError("; ".join(errors))
    return _load_manifest(manifest_path.resolve())


def signed_bundle_path_for_manifest(manifest_path: Path) -> Path:
    bundle = manifest_path.resolve().parent / SIGNED_BUNDLE_FILENAME
    if not bundle.is_file():
        raise BundleValidationError(f"missing {SIGNED_BUNDLE_FILENAME} beside release manifest")
    return bundle
