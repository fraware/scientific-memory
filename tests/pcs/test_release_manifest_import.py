"""ReleaseManifest.v0 import (PCS Phase 2 PR 1)."""

from __future__ import annotations

import json
import shutil
import tempfile
from pathlib import Path

import pytest

from sm_pipeline.pcs_import.release_manifest_importer import import_release_manifest
from sm_pipeline.pcs_validate.validator import BundleValidationError

from schema_fixtures import (
    EXPECTED_LABTRUST_CLAIM_ID,
    LABTRUST_RELEASE_DIR,
    copy_pcs_schemas,
)


def _copy_labtrust_release(tmp: Path) -> Path:
    dest = tmp / "labtrust-release"
    shutil.copytree(LABTRUST_RELEASE_DIR, dest)
    return dest


def test_import_release_manifest_valid() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        copy_pcs_schemas(root)
        release_dir = _copy_labtrust_release(root)
        manifest = release_dir / "ReleaseManifest.v0.json"
        result = import_release_manifest(
            manifest,
            repo_root=root,
            write=True,
            render=False,
        )
        assert result.claim_id == EXPECTED_LABTRUST_CLAIM_ID
        claim_dir = root / "corpus" / "pcs" / "claims" / result.claim_id
        assert (claim_dir / "release_manifest.json").is_file()
        report = json.loads(
            (claim_dir / "scientific_memory_import_report.json").read_text(encoding="utf-8"),
        )
        assert report["verification_status"] == "passed"
        assert report["strict"] is True
        assert report["allow_legacy"] is False
        assert report["bundle_shape"] == "pcs_core"
        assert report.get("release_id") == "release-pcs-v0.1-labtrust-qc"
        assert report.get("release_manifest_hash", "").startswith("sha256:")
        assert report.get("release_chain_validation_status") == "ProofChecked"
        assert report.get("release_chain_validation_id")
        assert "\\" not in report.get("source_bundle_path", "")
        assert report["source_bundle_path"].endswith("signed_science_claim_bundle.json")


def test_import_release_manifest_rejects_missing_signed_bundle() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        copy_pcs_schemas(root)
        release_dir = _copy_labtrust_release(root)
        (release_dir / "signed_science_claim_bundle.json").unlink()
        with pytest.raises(BundleValidationError, match="signed_science_claim_bundle"):
            import_release_manifest(
                release_dir / "ReleaseManifest.v0.json",
                repo_root=root,
                write=False,
                render=False,
            )


def test_import_release_manifest_rejects_hash_mismatch() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        copy_pcs_schemas(root)
        release_dir = _copy_labtrust_release(root)
        manifest_path = release_dir / "ReleaseManifest.v0.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["artifacts"]["trace.json"]["sha256"] = (
            "sha256:0000000000000000000000000000000000000000000000000000000000000000"
        )
        from sm_pipeline.pcs_validate.canonical_hash import canonical_hash

        manifest["signature_or_digest"] = canonical_hash(manifest)
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        with pytest.raises(BundleValidationError, match="digest mismatch"):
            import_release_manifest(
                manifest_path,
                repo_root=root,
                write=False,
                render=False,
            )


def test_import_release_manifest_rejects_placeholder_commit() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        copy_pcs_schemas(root)
        release_dir = _copy_labtrust_release(root)
        manifest_path = release_dir / "ReleaseManifest.v0.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["producer_repos"]["labtrust_gym"]["commit"] = (
            "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
        )
        from sm_pipeline.pcs_validate.canonical_hash import canonical_hash

        manifest["signature_or_digest"] = canonical_hash(manifest)
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        with pytest.raises(BundleValidationError, match="placeholder"):
            import_release_manifest(
                manifest_path,
                repo_root=root,
                write=False,
                render=False,
            )


def test_import_release_manifest_computes_report_without_fixture_overlay() -> None:
    """Release manifest import must not pin import report from sibling fixture."""
    from sm_pipeline.pcs_import.release_manifest_build import write_release_manifest

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        copy_pcs_schemas(root)
        release_dir = _copy_labtrust_release(root)
        report_path = release_dir / "scientific_memory_import_report.json"
        fixture_report = json.loads(report_path.read_text(encoding="utf-8"))
        fixture_report["release_id"] = "release-BOGUS-OVERLAY"
        report_path.write_text(json.dumps(fixture_report, indent=2) + "\n", encoding="utf-8")
        write_release_manifest(release_dir)

        import_release_manifest(
            release_dir / "ReleaseManifest.v0.json",
            repo_root=root,
            write=True,
            render=False,
        )
        claim_dir = root / "corpus" / "pcs" / "claims" / EXPECTED_LABTRUST_CLAIM_ID
        report = json.loads(
            (claim_dir / "scientific_memory_import_report.json").read_text(encoding="utf-8"),
        )
        assert report.get("release_id") == "release-pcs-v0.1-labtrust-qc"
        assert report.get("release_manifest_hash", "").startswith("sha256:")


def test_import_release_manifest_rejects_failed_verification() -> None:
    from sm_pipeline.pcs_validate.canonical_hash import canonical_hash, file_sha256_digest

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        copy_pcs_schemas(root)
        release_dir = _copy_labtrust_release(root)
        bundle_path = release_dir / "signed_science_claim_bundle.json"
        bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
        vr = bundle.get("verification_result")
        if isinstance(vr, dict):
            vr["status"] = "failed"
            checks = vr.get("checks")
            if isinstance(checks, list) and checks and isinstance(checks[0], dict):
                checks[0]["status"] = "failed"
        bundle_path.write_text(json.dumps(bundle, indent=2) + "\n", encoding="utf-8")
        manifest_path = release_dir / "ReleaseManifest.v0.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["artifacts"]["signed_science_claim_bundle.json"]["sha256"] = file_sha256_digest(
            bundle_path,
        )
        manifest["signature_or_digest"] = canonical_hash(manifest)
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        with pytest.raises(BundleValidationError, match="verification"):
            import_release_manifest(
                release_dir / "ReleaseManifest.v0.json",
                repo_root=root,
                write=False,
                render=False,
            )
