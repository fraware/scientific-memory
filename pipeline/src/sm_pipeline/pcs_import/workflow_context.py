"""Workflow-aware fields on PCS read models (domain-neutral)."""

from __future__ import annotations

from typing import Any

from sm_pipeline.pcs_import.workflow_profile import build_workflow_profile_view, load_workflow_profile


def apply_workflow_context(
    read_model: dict[str, Any],
    *,
    repo_root: Any,
    validation: dict[str, Any] | None,
    lineage: dict[str, Any] | None,
    release_dir: Any | None = None,
    manifest: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Set top-level workflow_id, domain, artifact type lists, and workflow_profile view."""
    out = dict(read_model)
    profile_id = ""
    if isinstance(validation, dict):
        profile_id = str(validation.get("workflow_profile_id") or "")
    if not profile_id and isinstance(lineage, dict):
        profile_id = str(lineage.get("workflow_profile_id") or "")

    profile: dict[str, Any] | None = None
    if release_dir is not None:
        from pathlib import Path

        release_path = Path(release_dir)
        for name in ("workflow_profile.v0.json", "WorkflowProfile.v0.json"):
            path = release_path / name
            if path.is_file():
                import json

                data = json.loads(path.read_text(encoding="utf-8-sig"))
                if isinstance(data, dict):
                    profile = data
                    if not profile_id:
                        profile_id = str(data.get("workflow_id") or "")
                break

    if profile is None and profile_id and repo_root is not None:
        from pathlib import Path

        profile = load_workflow_profile(profile_id, repo_root=Path(repo_root))

    if profile is not None:
        view = build_workflow_profile_view(profile)
        out["workflow_profile"] = view
        out["workflow_id"] = view.get("workflow_id") or profile_id
        out["domain"] = view.get("domain")
        out["runtime_artifact_types"] = list(view.get("runtime_artifacts") or [])
        out["certificate_artifact_types"] = list(view.get("certificate_artifacts") or [])
    elif profile_id:
        out["workflow_id"] = profile_id

    from sm_pipeline.pcs_import.computation_protocol import (
        COMPUTATION_LIMITATION_NOTICE,
        is_computation_workflow,
    )

    workflow_key = str(out.get("workflow_id") or profile_id or "")
    if is_computation_workflow(workflow_key):
        limitations = list(out.get("limitations") or [])
        if COMPUTATION_LIMITATION_NOTICE not in limitations:
            limitations.append(COMPUTATION_LIMITATION_NOTICE)
        out["limitations"] = limitations
        out["limitation_notice"] = COMPUTATION_LIMITATION_NOTICE
    elif isinstance(manifest, dict) and manifest.get("limitations_notice"):
        notice = str(manifest["limitations_notice"])
        limitations = list(out.get("limitations") or [])
        if notice not in limitations:
            limitations.append(notice)
        out["limitations"] = limitations
        if not out.get("limitation_notice"):
            out["limitation_notice"] = notice

    return out
