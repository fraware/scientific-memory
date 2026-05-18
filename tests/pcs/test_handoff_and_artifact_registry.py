"""HandoffManifest.v0 consumer and ArtifactRegistry.v0 first-class loading."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from schema_fixtures import (
    CANONICAL_RC_SCIENTIFIC_MEMORY_COMMIT,
    LABTRUST_RELEASE_DIR,
    LABTRUST_RELEASE_MANIFEST_V0,
    REPO_ROOT,
    resolve_pcs_core_root,
)

pytestmark = pytest.mark.skipif(
    not resolve_pcs_core_root().is_dir(),
    reason="pcs-core not available",
)

PCS_LABTRUST = resolve_pcs_core_root() / "examples" / "labtrust-release"


def test_handoff_manifests_discovered_in_fixtures() -> None:
    from sm_pipeline.pcs_validate.handoff_manifest import discover_handoff_manifests

    paths = discover_handoff_manifests(LABTRUST_RELEASE_DIR)
    pcs_paths = discover_handoff_manifests(PCS_LABTRUST)
    assert len(paths) == len(pcs_paths) == 4


def test_handoff_manifests_validate() -> None:
    from sm_pipeline.pcs_validate.handoff_manifest import validate_handoff_manifest

    for path in sorted(LABTRUST_RELEASE_DIR.glob("handoff_manifest.*.v0.json")):
        errors = validate_handoff_manifest(path, repo_root=REPO_ROOT)
        assert errors == [], f"{path.name}: {errors}"


def test_load_release_handoffs() -> None:
    from sm_pipeline.pcs_import.handoff_manifest import load_release_handoffs

    handoffs = load_release_handoffs(LABTRUST_RELEASE_DIR, repo_root=REPO_ROOT)
    assert len(handoffs) == 4
    kinds = {h["handoff_kind"] for h in handoffs}
    assert "runtime_to_certificate" in kinds
    assert "signed_bundle_to_memory" in kinds


def test_artifact_registry_v0_loads_first_class() -> None:
    from sm_pipeline.pcs_import.artifact_registry_source import (
        REGISTRY_SOURCE_V0,
        load_artifact_registry_v0,
    )

    registry_path = LABTRUST_RELEASE_DIR / "ArtifactRegistry.v0.json"
    if not registry_path.is_file():
        pytest.skip("ArtifactRegistry.v0.json not synced yet")

    registry, version, source = load_artifact_registry_v0(
        REPO_ROOT,
        release_dir=LABTRUST_RELEASE_DIR,
        validate=True,
    )
    assert registry is not None
    assert version == "0.1.0"
    assert source in (REGISTRY_SOURCE_V0, "artifact_registry.valid.json")
    assert isinstance(registry.get("entries"), dict)
    assert registry.get("registry_id")


def test_release_manifest_scientific_memory_matches_pcs_core() -> None:
    pcs_manifest_path = PCS_LABTRUST / "release_manifest.v0.json"
    if not pcs_manifest_path.is_file():
        pytest.skip("pcs-core release manifest missing")
    pcs = json.loads(pcs_manifest_path.read_text(encoding="utf-8-sig"))
    sm = json.loads(LABTRUST_RELEASE_MANIFEST_V0.read_text(encoding="utf-8-sig"))
    pcs_commit = pcs["producer_repos"]["scientific_memory"]["commit"]
    sm_commit = sm["producer_repos"]["scientific_memory"]["commit"]
    assert sm_commit == pcs_commit
    assert sm_commit == CANONICAL_RC_SCIENTIFIC_MEMORY_COMMIT


def test_finalize_persists_registry_and_handoffs(tmp_path: Path) -> None:
    from sm_pipeline.pcs_import.release_mode_finalize import finalize_release_mode_claim
    from sm_pipeline.pcs_validate.release_chain_validation import require_release_chain_validation

    release_dir = LABTRUST_RELEASE_DIR
    bundle = release_dir / "signed_science_claim_bundle.json"
    claim_dir = tmp_path / "claim-pcs-qc-release-v0.1"
    claim_dir.mkdir()
    (claim_dir / "read_model.json").write_text(
        json.dumps({"claim_id": "claim-pcs-qc-release-v0.1"}) + "\n",
        encoding="utf-8",
    )
    report_path = claim_dir / "scientific_memory_import_report.json"
    shutil_copy_report = release_dir / "scientific_memory_import_report.json"
    report_path.write_text(shutil_copy_report.read_text(encoding="utf-8"), encoding="utf-8")

    validation = require_release_chain_validation(release_dir, repo_root=REPO_ROOT)
    finalize_release_mode_claim(
        claim_dir,
        bundle,
        repo_root=REPO_ROOT,
        release_validation=validation,
        import_report_path=report_path,
    )

    if (release_dir / "ArtifactRegistry.v0.json").is_file():
        assert (claim_dir / "artifact_registry.json").is_file()
    if list(release_dir.glob("handoff_manifest.*.v0.json")):
        assert (claim_dir / "handoff_manifests.json").is_file()
        handoffs = json.loads((claim_dir / "handoff_manifests.json").read_text())
        assert len(handoffs) >= 1
