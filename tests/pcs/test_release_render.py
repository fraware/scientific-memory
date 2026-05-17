"""Portal render sections for release protocol metadata (PCS Phase 2 PR 3)."""

from __future__ import annotations

import json
import shutil
import tempfile
from pathlib import Path

from sm_pipeline.pcs_import.release_manifest_importer import import_release_manifest

from schema_fixtures import (
    EXPECTED_LABTRUST_CLAIM_ID,
    LABTRUST_RELEASE_DIR,
    copy_pcs_schemas,
)


def _import_release_read_model() -> dict:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        copy_pcs_schemas(root)
        release_dir = root / "labtrust-release"
        shutil.copytree(LABTRUST_RELEASE_DIR, release_dir)
        import_release_manifest(
            release_dir / "ReleaseManifest.v0.json",
            repo_root=root,
            write=True,
            render=False,
        )
        path = (
            root
            / "corpus"
            / "pcs"
            / "claims"
            / EXPECTED_LABTRUST_CLAIM_ID
            / "read_model.json"
        )
        return json.loads(path.read_text(encoding="utf-8"))


def test_render_release_manifest_section() -> None:
    model = _import_release_read_model()
    manifest = model.get("release_manifest")
    assert isinstance(manifest, dict)
    assert manifest.get("release_id") == "release-pcs-v0.1-labtrust-qc"
    assert manifest.get("release_status") == "Validated"
    assert str(manifest.get("manifest_hash", "")).startswith("sha256:")


def test_render_release_chain_validation_section() -> None:
    model = _import_release_read_model()
    validation = model.get("release_chain_validation")
    assert isinstance(validation, dict)
    assert validation.get("status") == "ProofChecked"
    assert validation.get("validation_id") == "validation-pcs-v0.1-labtrust-qc-rc"
    assert isinstance(validation.get("checks"), list) and validation["checks"]


def test_render_artifact_registry_metadata() -> None:
    model = _import_release_read_model()
    registry = model.get("artifact_registry")
    assert isinstance(registry, list) and registry
    signed = next(row for row in registry if row["name"] == "signed_science_claim_bundle.json")
    assert signed["artifact_type"] == "SignedScienceClaimBundle.v0"
    assert signed["producer"]
    assert signed["schema"]
    assert signed["hash"].startswith("sha256:")
    assert signed["source_repo"]
    assert signed["source_commit"]


def test_render_artifact_dependency_graph() -> None:
    model = _import_release_read_model()
    graph = model.get("artifact_dependency_graph")
    assert isinstance(graph, list) and len(graph) >= 2
    assert graph[0]["from"]
    assert graph[0]["to"]
    assert graph[0]["kind"] == "release_chain"
