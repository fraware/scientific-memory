"""Validate HandoffManifest.v0 (pcs-core consumer)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from sm_pipeline.pcs_validate.pcs_core_hook import pcs_core_available, validate_protocol_artifact
from sm_pipeline.pcs_validate.placeholder_commits import validate_source_commit_for_release
from sm_pipeline.pcs_validate.validator import BundleValidationError, validator_for

HANDOFF_MANIFEST_SCHEMA = "HandoffManifest.v0.schema.json"
HANDOFF_GLOB = "handoff_manifest.*.v0.json"


def _load_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as exc:
        raise BundleValidationError(f"Handoff manifest JSON parse error: {exc}") from exc
    if not isinstance(data, dict):
        raise BundleValidationError("Handoff manifest root must be a JSON object")
    return data


def _validate_schema(data: dict[str, Any], repo_root: Path) -> list[str]:
    if pcs_core_available():
        return validate_protocol_artifact(data, "HandoffManifest.v0")
    errors: list[str] = []
    try:
        validator = validator_for(HANDOFF_MANIFEST_SCHEMA, repo_root)
    except FileNotFoundError as exc:
        return [str(exc)]
    for err in sorted(validator.iter_errors(data), key=lambda item: item.path):
        errors.append(err.message)
    return errors


def validate_handoff_manifest(
    path: Path,
    *,
    repo_root: Path | None = None,
) -> list[str]:
    path = path.resolve()
    if not path.is_file():
        return [f"missing handoff manifest: {path}"]
    root = repo_root or Path(__file__).resolve().parents[4]
    try:
        data = _load_json(path)
    except BundleValidationError as exc:
        return [str(exc)]
    errors = _validate_schema(data, root)
    commit = data.get("source_commit")
    if isinstance(commit, str):
        msg = validate_source_commit_for_release(commit, path="source_commit")
        if msg:
            errors.append(msg)
    if data.get("status") != "Validated":
        errors.append(f"handoff status must be Validated for release import (got {data.get('status')!r})")
    inputs = data.get("input_artifacts")
    if isinstance(inputs, dict):
        for name, entry in inputs.items():
            if isinstance(entry, dict) and not entry.get("sha256"):
                errors.append(f"input_artifacts.{name}: sha256 required when status is Validated")
    return errors


def validate_handoff_manifest_or_raise(path: Path, *, repo_root: Path | None = None) -> dict[str, Any]:
    errors = validate_handoff_manifest(path, repo_root=repo_root)
    if errors:
        raise BundleValidationError("; ".join(errors))
    return _load_json(path.resolve())


def discover_handoff_manifests(release_dir: Path) -> list[Path]:
    return sorted(release_dir.resolve().glob(HANDOFF_GLOB))
