"""Claim lineage and stale tracking (PCS Phase 2 PR 4)."""

from __future__ import annotations

import json
import shutil
import tempfile
from pathlib import Path

from sm_pipeline.pcs_import.claim_lineage import (
    build_lineage,
    check_stale,
    update_lineage_stale_flags,
    write_lineage,
)
from sm_pipeline.pcs_import.claim_query import list_claims_by_certificate
from sm_pipeline.pcs_import.release_manifest_importer import import_release_manifest
from sm_pipeline.pcs_validate.canonical_hash import canonical_hash, file_sha256_digest

from schema_fixtures import (
    CANONICAL_RC_CERTIFICATE_ID,
    EXPECTED_LABTRUST_CLAIM_ID,
    LABTRUST_RELEASE_BUNDLE,
    LABTRUST_RELEASE_DIR,
    LABTRUST_RELEASE_MANIFEST_V0,
    copy_pcs_schemas,
)


def _import_claim(root: Path) -> Path:
    release_dir = root / "labtrust-release"
    shutil.copytree(LABTRUST_RELEASE_DIR, release_dir)
    import_release_manifest(
        release_dir / "ReleaseManifest.v0.json",
        repo_root=root,
        write=True,
        render=False,
    )
    return root / "corpus" / "pcs" / "claims" / EXPECTED_LABTRUST_CLAIM_ID


def test_claim_lineage_records_certificate_id() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        copy_pcs_schemas(root)
        claim_dir = _import_claim(root)
        lineage = json.loads((claim_dir / "lineage.json").read_text(encoding="utf-8"))
        assert lineage["certificate_id"] == CANONICAL_RC_CERTIFICATE_ID


def test_claim_lineage_records_release_manifest_hash() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        copy_pcs_schemas(root)
        claim_dir = _import_claim(root)
        manifest = json.loads((claim_dir / "release_manifest.json").read_text(encoding="utf-8"))
        lineage = json.loads((claim_dir / "lineage.json").read_text(encoding="utf-8"))
        assert lineage["release_manifest_hash"] == canonical_hash(manifest)


def test_claim_marked_stale_when_certificate_changes() -> None:
    bundle = json.loads(LABTRUST_RELEASE_BUNDLE.read_text(encoding="utf-8-sig"))
    manifest = json.loads(LABTRUST_RELEASE_MANIFEST_V0.read_text(encoding="utf-8-sig"))
    lineage = build_lineage(
        claim_id=EXPECTED_LABTRUST_CLAIM_ID,
        bundle=bundle,
        signed_bundle_path=LABTRUST_RELEASE_BUNDLE,
        release_manifest=manifest,
    )
    stale, reasons = check_stale(
        lineage,
        current_certificate_id="cert-tampered",
        current_bundle_hash=lineage["signed_bundle_hash"],
    )
    assert stale
    assert any("certificate_id" in reason for reason in reasons)


def test_claim_marked_stale_when_signed_bundle_hash_changes() -> None:
    bundle = json.loads(LABTRUST_RELEASE_BUNDLE.read_text(encoding="utf-8-sig"))
    manifest = json.loads(LABTRUST_RELEASE_MANIFEST_V0.read_text(encoding="utf-8-sig"))
    lineage = build_lineage(
        claim_id=EXPECTED_LABTRUST_CLAIM_ID,
        bundle=bundle,
        signed_bundle_path=LABTRUST_RELEASE_BUNDLE,
        release_manifest=manifest,
    )
    stale, reasons = check_stale(
        lineage,
        current_bundle_hash="sha256:" + "f" * 64,
        current_certificate_id=lineage["certificate_id"],
    )
    assert stale
    assert any("signed_bundle_hash" in reason for reason in reasons)


def test_claim_query_by_certificate_id() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        copy_pcs_schemas(root)
        _import_claim(root)
        matches = list_claims_by_certificate(root, CANONICAL_RC_CERTIFICATE_ID)
        assert EXPECTED_LABTRUST_CLAIM_ID in matches


def test_update_lineage_stale_flags_on_disk() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        copy_pcs_schemas(root)
        claim_dir = _import_claim(root)
        bundle_path = claim_dir / "signed_bundle.json"
        bundle = json.loads(bundle_path.read_text(encoding="utf-8-sig"))
        bundle["science_claim_bundle"]["certificates"][0]["certificate_id"] = "cert-changed"
        bundle_path.write_text(json.dumps(bundle, indent=2) + "\n", encoding="utf-8")
        lineage = update_lineage_stale_flags(claim_dir, bundle_path=bundle_path)
        assert lineage["stale"] is True
        assert lineage["signed_bundle_hash"] != file_sha256_digest(bundle_path)
