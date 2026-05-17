"""ReleaseChainValidationResult.v0 requirements (PCS Phase 2 PR 2)."""

from __future__ import annotations

import json
import shutil
import tempfile
from pathlib import Path

import pytest

from sm_pipeline.pcs_import.release_manifest_importer import import_release_manifest
from sm_pipeline.pcs_import.science_claim_bundle_importer import import_signed_bundle
from sm_pipeline.pcs_validate.canonical_hash import canonical_hash
from sm_pipeline.pcs_validate.validator import BundleValidationError

from schema_fixtures import (
    EXPECTED_LABTRUST_CLAIM_ID,
    LABTRUST_RELEASE_BUNDLE,
    LABTRUST_RELEASE_CHAIN_VALIDATION,
    LABTRUST_RELEASE_DIR,
    copy_pcs_schemas,
)


def _copy_release_dir(tmp: Path) -> Path:
    dest = tmp / "labtrust-release"
    shutil.copytree(LABTRUST_RELEASE_DIR, dest)
    return dest


def test_import_requires_release_chain_validation_result_in_release_mode() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        copy_pcs_schemas(root)
        release_dir = _copy_release_dir(root)
        (release_dir / "ReleaseChainValidationResult.v0.json").unlink()
        with pytest.raises(BundleValidationError, match="missing release chain validation"):
            import_signed_bundle(
                release_dir / "signed_science_claim_bundle.json",
                repo_root=root,
                strict=True,
                release_mode=True,
                write=False,
            )


def test_import_rejects_rejected_release_chain_result() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        copy_pcs_schemas(root)
        release_dir = _copy_release_dir(root)
        validation_path = release_dir / "ReleaseChainValidationResult.v0.json"
        validation = json.loads(validation_path.read_text(encoding="utf-8"))
        validation["status"] = "Rejected"
        validation["checks"][0]["status"] = "failed"
        validation["failure_codes"] = ["manifest_hash_alignment"]
        validation["signature_or_digest"] = canonical_hash(validation)
        validation_path.write_text(json.dumps(validation, indent=2) + "\n", encoding="utf-8")
        with pytest.raises(BundleValidationError, match="ProofChecked"):
            import_release_manifest(
                release_dir / "ReleaseManifest.v0.json",
                repo_root=root,
                write=False,
                render=False,
            )


def test_import_report_records_release_chain_validation_status() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        copy_pcs_schemas(root)
        release_dir = _copy_release_dir(root)
        import_release_manifest(
            release_dir / "ReleaseManifest.v0.json",
            repo_root=root,
            write=True,
            render=False,
        )
        report_path = (
            root
            / "corpus"
            / "pcs"
            / "claims"
            / EXPECTED_LABTRUST_CLAIM_ID
            / "scientific_memory_import_report.json"
        )
        validation = json.loads(
            (release_dir / "ReleaseChainValidationResult.v0.json").read_text(encoding="utf-8"),
        )
        report = json.loads(report_path.read_text(encoding="utf-8"))
        assert report["release_chain_validation_status"] == "ProofChecked"
        assert report["release_chain_validation_id"] == validation["validation_id"]
        assert report["release_chain_validator"] == validation["validator"]
        assert report["release_chain_checked_at"] == validation["checked_at"]
