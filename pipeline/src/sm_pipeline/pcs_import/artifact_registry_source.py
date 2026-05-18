"""Resolve PCS ArtifactRegistry.v0 (first-class when present, else legacy valid.json)."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from sm_pipeline.pcs_validate.artifact_registry import validate_artifact_registry_or_raise

DERIVED_REGISTRY_VERSION = "derived-ReleaseManifest.v0"
REGISTRY_SOURCE_DERIVED = "derived-ReleaseManifest.v0"
REGISTRY_SOURCE_VALID = "artifact_registry.valid.json"
REGISTRY_SOURCE_V0 = "ArtifactRegistry.v0"


def _pcs_core_examples(repo_root: Path) -> Path | None:
    env = os.environ.get("PCS_CORE_PATH", "").strip()
    if env:
        candidate = Path(env) / "examples"
        if candidate.is_dir():
            return candidate
    sibling = repo_root.parent / "pcs-core" / "examples"
    if sibling.is_dir():
        return sibling
    return None


def _pcs_labtrust_release(repo_root: Path) -> Path | None:
    examples = _pcs_core_examples(repo_root)
    if examples is None:
        return None
    path = examples / "labtrust-release"
    return path if path.is_dir() else None


def resolve_artifact_registry_path(release_dir: Path | None, repo_root: Path) -> Path | None:
    if release_dir is not None:
        for name in ("ArtifactRegistry.v0.json", "artifact_registry.v0.json"):
            candidate = release_dir / name
            if candidate.is_file():
                return candidate
    examples = _pcs_core_examples(repo_root)
    if examples is not None:
        for name in (
            "ArtifactRegistry.v0.json",
            "artifact_registry.v0.json",
            "artifact_registry.valid.json",
        ):
            candidate = examples / name
            if candidate.is_file():
                return candidate
        labtrust = examples / "labtrust-release"
        if labtrust.is_dir():
            for name in ("ArtifactRegistry.v0.json", "artifact_registry.v0.json"):
                candidate = labtrust / name
                if candidate.is_file():
                    return candidate
    for vendored in (
        repo_root / "schemas" / "pcs" / "ArtifactRegistry.v0.json",
        repo_root / "schemas" / "pcs" / "artifact_registry.valid.json",
    ):
        if vendored.is_file():
            return vendored
    return None


def _registry_source_label(path: Path) -> str:
    name = path.name.lower()
    if "artifactregistry.v0" in name.replace("_", "").replace("-", ""):
        return REGISTRY_SOURCE_V0
    if "valid" in name:
        return REGISTRY_SOURCE_VALID
    return name


def load_artifact_registry_v0(
    repo_root: Path,
    *,
    release_dir: Path | None = None,
    validate: bool = True,
) -> tuple[dict[str, Any] | None, str, str]:
    """
    Return (registry artifact, registry_version, source label).

    When no ArtifactRegistry.v0 file is present, returns (None, DERIVED, REGISTRY_SOURCE_DERIVED).
    """
    root = repo_root.resolve()
    path = resolve_artifact_registry_path(release_dir, root)
    if path is None:
        return None, DERIVED_REGISTRY_VERSION, REGISTRY_SOURCE_DERIVED
    data = (
        validate_artifact_registry_or_raise(path, repo_root=root)
        if validate
        else json.loads(path.read_text(encoding="utf-8-sig"))
    )
    version = str(data.get("registry_version") or data.get("schema_version") or "0.1.0")
    return data, version, _registry_source_label(path)


def load_pcs_core_artifact_registry(repo_root: Path) -> tuple[dict[str, Any], str]:
    """Backward-compatible: entries keyed by artifact_type."""
    registry, version, _ = load_artifact_registry_v0(repo_root, validate=False)
    if registry is None:
        return {}, DERIVED_REGISTRY_VERSION
    entries = registry.get("entries")
    if isinstance(entries, dict):
        return entries, version
    return {}, version


def registry_entries_by_type(registry: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(registry, dict):
        return {}
    entries = registry.get("entries")
    return entries if isinstance(entries, dict) else {}


def semantic_check_labels(spec_checks: Any) -> list[str]:
    labels: list[str] = []
    if not isinstance(spec_checks, list):
        return labels
    for check in spec_checks:
        if isinstance(check, dict):
            label = str(check.get("check_id") or check.get("description") or "")
            if label:
                labels.append(label)
        elif isinstance(check, str) and check:
            labels.append(check)
    return labels
