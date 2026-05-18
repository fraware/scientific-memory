"""Workflow profile loading and read-model enrichment."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from sm_pipeline.pcs_import.release_manifest_importer import import_release_manifest
from sm_pipeline.pcs_import.workflow_profile import build_workflow_profile_view, load_workflow_profile

from schema_fixtures import EXPECTED_LABTRUST_CLAIM_ID, LABTRUST_RELEASE_DIR, copy_pcs_schemas


def test_load_labtrust_workflow_profile() -> None:
    root = Path(__file__).resolve().parents[2]
    profile = load_workflow_profile("labtrust.qc_release_v0.1", repo_root=root)
    assert profile is not None
    assert profile.get("workflow_id") == "labtrust.qc_release_v0.1"
    view = build_workflow_profile_view(profile)
    assert view["domain"] == "lab_science_simulation"
    assert "RuntimeReceipt.v0" in (view.get("runtime_artifacts") or [])


def test_import_includes_workflow_profile_in_read_model(tmp_path: Path) -> None:
    root = tmp_path
    copy_pcs_schemas(root)
    release_dir = root / "labtrust-release"
    shutil.copytree(LABTRUST_RELEASE_DIR, release_dir)
    import_release_manifest(
        release_dir / "ReleaseManifest.v0.json",
        repo_root=root,
        write=True,
        render=False,
    )
    read_model = json.loads(
        (
            root / "corpus" / "pcs" / "claims" / EXPECTED_LABTRUST_CLAIM_ID / "read_model.json"
        ).read_text(encoding="utf-8"),
    )
    profile = read_model.get("workflow_profile")
    assert isinstance(profile, dict)
    assert profile.get("workflow_id") == "labtrust.qc_release_v0.1"
    lineage = json.loads(
        (
            root / "corpus" / "pcs" / "claims" / EXPECTED_LABTRUST_CLAIM_ID / "lineage.json"
        ).read_text(encoding="utf-8"),
    )
    assert lineage.get("workflow_profile_id") == "labtrust.qc_release_v0.1"
