"""Load WorkflowProfile.v0 for release evidence rendering."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any


def _workflow_profile_dirs(repo_root: Path) -> list[Path]:
    dirs: list[Path] = []
    env = os.environ.get("PCS_CORE_PATH", "").strip()
    if env:
        candidate = Path(env) / "examples" / "workflow_profiles"
        if candidate.is_dir():
            dirs.append(candidate)
    sibling = repo_root.parent / "pcs-core" / "examples" / "workflow_profiles"
    if sibling.is_dir():
        dirs.append(sibling)
    vendored = repo_root / "schemas" / "pcs" / "workflow_profiles"
    if vendored.is_dir():
        dirs.append(vendored)
    return dirs


def load_workflow_profile(
    workflow_profile_id: str,
    *,
    repo_root: Path,
) -> dict[str, Any] | None:
    """Resolve WorkflowProfile.v0 by workflow_id (profile id)."""
    if not workflow_profile_id:
        return None
    try:
        from pcs_core.workflow_profiles import load_workflow_profile as pcs_load

        profile = pcs_load(workflow_profile_id)
        if isinstance(profile, dict):
            return profile
    except ImportError:
        pass

    for directory in _workflow_profile_dirs(repo_root.resolve()):
        for path in sorted(directory.glob("*.json")):
            try:
                data = json.loads(path.read_text(encoding="utf-8-sig"))
            except json.JSONDecodeError:
                continue
            if isinstance(data, dict) and data.get("workflow_id") == workflow_profile_id:
                return data
    return None


def build_workflow_profile_view(profile: dict[str, Any]) -> dict[str, Any]:
    """Domain-neutral portal view for WorkflowProfile.v0."""
    return {
        "workflow_id": profile.get("workflow_id"),
        "domain": profile.get("domain"),
        "description": profile.get("description"),
        "runtime_artifacts": list(profile.get("runtime_artifacts") or []),
        "certificate_artifacts": list(profile.get("certificate_artifacts") or []),
        "handoff_sequence": list(profile.get("handoff_sequence") or []),
        "required_registry_entries": list(profile.get("required_registry_entries") or []),
        "limitations_notice": profile.get("limitations_notice"),
        "signature_or_digest": profile.get("signature_or_digest"),
        "schema_version": profile.get("schema_version"),
        "payload": profile,
    }
