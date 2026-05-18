"""Load and normalize HandoffManifest.v0 artifacts beside a release."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from sm_pipeline.pcs_validate.handoff_manifest import (
    discover_handoff_manifests,
    validate_handoff_manifest_or_raise,
)


def load_release_handoffs(
    release_dir: Path,
    *,
    repo_root: Path | None = None,
) -> list[dict[str, Any]]:
    handoffs: list[dict[str, Any]] = []
    for path in discover_handoff_manifests(release_dir):
        data = validate_handoff_manifest_or_raise(path, repo_root=repo_root)
        view = build_handoff_manifest_view(data, path)
        handoffs.append(view)
    return handoffs


def build_handoff_manifest_view(data: dict[str, Any], path: Path | None = None) -> dict[str, Any]:
    inputs_out: list[dict[str, Any]] = []
    for name, entry in sorted((data.get("input_artifacts") or {}).items()):
        if isinstance(entry, dict):
            inputs_out.append(
                {
                    "name": name,
                    "artifact_type": entry.get("artifact_type", ""),
                    "sha256": entry.get("sha256", ""),
                },
            )
    outputs_out: list[dict[str, Any]] = []
    for name, entry in sorted((data.get("expected_outputs") or {}).items()):
        if isinstance(entry, dict):
            outputs_out.append(
                {
                    "name": name,
                    "artifact_type": entry.get("artifact_type", ""),
                    "sha256": entry.get("sha256", ""),
                },
            )
    return {
        "handoff_id": data.get("handoff_id"),
        "handoff_kind": data.get("handoff_kind"),
        "from_component": data.get("from_component"),
        "to_component": data.get("to_component"),
        "created_at": data.get("created_at"),
        "source_repo": data.get("source_repo"),
        "source_commit": data.get("source_commit"),
        "status": data.get("status"),
        "signature_or_digest": data.get("signature_or_digest"),
        "input_artifacts": inputs_out,
        "expected_outputs": outputs_out,
        "invariants": dict(data.get("invariants") or {}),
        "manifest_path": str(path.name) if path is not None else "",
    }


def build_handoff_dependency_edges(handoffs: list[dict[str, Any]]) -> list[dict[str, str]]:
    edges: list[dict[str, str]] = []
    for handoff in handoffs:
        from_component = str(handoff.get("from_component") or "")
        to_component = str(handoff.get("to_component") or "")
        kind = str(handoff.get("handoff_kind") or "handoff")
        if from_component and to_component:
            edges.append(
                {
                    "from": from_component,
                    "to": to_component,
                    "kind": kind,
                    "handoff_id": str(handoff.get("handoff_id") or ""),
                },
            )
    return edges
