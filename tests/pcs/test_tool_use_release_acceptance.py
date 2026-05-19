"""Tool-use safety release import and workflow-aware read model."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from sm_pipeline.pcs_import.release_manifest_importer import import_release_manifest
from sm_pipeline.pcs_validate.release_paths import resolve_release_manifest_path

from schema_fixtures import REPO_ROOT, copy_pcs_schemas

TOOL_USE_FIXTURE = REPO_ROOT / "tests" / "pcs" / "fixtures" / "tool-use-release"


@pytest.fixture(scope="module")
def tool_use_release_dir() -> Path:
    if not TOOL_USE_FIXTURE.is_dir():
        pytest.skip("tool-use fixtures missing; run: python scripts/sync_tool_use_release_from_pcs_core.py --ensure")
    manifest = resolve_release_manifest_path(TOOL_USE_FIXTURE)
    if not manifest.is_file():
        pytest.skip("tool-use release manifest missing")
    return TOOL_USE_FIXTURE


def test_tool_use_manifest_resolves_release_manifest(tool_use_release_dir: Path) -> None:
    path = resolve_release_manifest_path(tool_use_release_dir)
    assert path.name in ("release_manifest.v0.json", "ReleaseManifest.v0.json")


def test_tool_use_release_import_read_model(tmp_path: Path, tool_use_release_dir: Path) -> None:
    root = tmp_path
    copy_pcs_schemas(root)
    for name in ("schemas",):
        vendored = REPO_ROOT / name
        if vendored.is_dir():
            dest = root / name
            if dest.exists():
                shutil.rmtree(dest)
            shutil.copytree(vendored, dest)

    manifest_path = resolve_release_manifest_path(tool_use_release_dir)
    release_copy = root / "release"
    shutil.copytree(tool_use_release_dir, release_copy)
    manifest_copy = resolve_release_manifest_path(release_copy)

    result = import_release_manifest(manifest_copy, repo_root=root, write=True, render=False)
    claim_dir = root / "corpus" / "pcs" / "claims" / result.claim_id
    read_model = json.loads((claim_dir / "read_model.json").read_text(encoding="utf-8-sig"))

    assert read_model.get("workflow_id") == "agent_tool_use.safety_v0"
    assert read_model.get("domain") == "agent_tool_use"
    assert "ToolUseTrace.v0" in (read_model.get("runtime_artifact_types") or [])
    assert "ToolUseCertificate.v0" in (read_model.get("certificate_artifact_types") or [])
    assert read_model.get("tool_use_trace")
    assert read_model.get("tool_use_certificate")
    assert read_model.get("release_manifest")
    assert read_model.get("release_chain_validation")
    assert read_model.get("workflow_profile")
    kernel = read_model.get("formal_trust_kernel")
    assert isinstance(kernel, dict)
    assert kernel.get("overall_status") == "ProofChecked"
    assert len(kernel.get("lean_check_results") or []) >= 5

    for name in (
        "signed_bundle.json",
        "read_model.json",
        "import_manifest.json",
        "scientific_memory_import_report.json",
        "lineage.json",
        "release_manifest.json",
        "release_chain_validation.json",
    ):
        assert (claim_dir / name).is_file(), name


def test_tool_use_phase2_read_model_fixture_matches_import(tmp_path: Path, tool_use_release_dir: Path) -> None:
    fixture_model = tool_use_release_dir / ".phase2-read-model.json"
    if not fixture_model.is_file():
        pytest.skip("run: just sync-tool-use-release")

    root = tmp_path
    copy_pcs_schemas(root)
    import shutil

    release_copy = root / "release"
    shutil.copytree(tool_use_release_dir, release_copy)
    manifest_copy = resolve_release_manifest_path(release_copy)
    result = import_release_manifest(manifest_copy, repo_root=root, write=True, render=False)
    imported = json.loads(
        (root / "corpus" / "pcs" / "claims" / result.claim_id / "read_model.json").read_text(
            encoding="utf-8-sig",
        ),
    )
    golden = json.loads(fixture_model.read_text(encoding="utf-8-sig"))
    assert imported["workflow_id"] == golden["workflow_id"]
    assert imported["domain"] == golden["domain"]
    assert imported["tool_use_trace"]["id"] == golden["tool_use_trace"]["id"]
    assert imported["tool_use_certificate"]["id"] == golden["tool_use_certificate"]["id"]
    assert (
        imported["release_manifest"]["release_id"]
        == golden["release_manifest"]["release_id"]
    )
