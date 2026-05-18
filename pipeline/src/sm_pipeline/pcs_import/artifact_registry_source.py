"""Resolve PCS artifact registry metadata (pcs-core example or manifest-derived)."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

DERIVED_REGISTRY_VERSION = "derived-ReleaseManifest.v0"


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


def load_pcs_core_artifact_registry(repo_root: Path) -> tuple[dict[str, Any], str]:
    """Return (entries by artifact_type, registry_version)."""
    examples = _pcs_core_examples(repo_root)
    if examples is None:
        return {}, DERIVED_REGISTRY_VERSION

    for name in ("artifact_registry.valid.json", "ArtifactRegistry.v0.json"):
        path = examples / name
        if not path.is_file():
            continue
        data = json.loads(path.read_text(encoding="utf-8-sig"))
        if not isinstance(data, dict):
            continue
        entries = data.get("entries")
        if isinstance(entries, dict):
            version = str(data.get("registry_version") or data.get("schema_version") or "0.1.0")
            return entries, version

    vendored = repo_root / "schemas" / "pcs" / "artifact_registry.valid.json"
    if vendored.is_file():
        data = json.loads(vendored.read_text(encoding="utf-8-sig"))
        if isinstance(data, dict) and isinstance(data.get("entries"), dict):
            version = str(data.get("registry_version") or "0.1.0")
            return data["entries"], version

    return {}, DERIVED_REGISTRY_VERSION
