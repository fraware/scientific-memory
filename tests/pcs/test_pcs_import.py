"""PCS import contract tests (PF canonical fixture; strict mode frozen)."""

import json
import tempfile
from pathlib import Path

import pytest

from sm_pipeline.pcs_import.science_claim_bundle_importer import import_signed_bundle
from sm_pipeline.pcs_validate.placeholder_commits import is_placeholder_commit
from sm_pipeline.pcs_validate.validator import BundleValidationError

from schema_fixtures import (
    EXPECTED_LABTRUST_CLAIM_ID,
    IMPORT_REPORT_REQUIRED_KEYS,
    LABTRUST_RELEASE_BUNDLE,
    LABTRUST_RELEASE_MANIFEST,
    LEGACY_SIGNED_BUNDLE,
    PF_SIGNED_BUNDLE,
    copy_pcs_schemas,
)

FIXTURES = Path(__file__).resolve().parent / "fixtures"


def test_import_pf_signed_bundle_valid() -> None:
    assert PF_SIGNED_BUNDLE.is_file(), (
        "missing labtrust-release fixture; copy from provability-fabric/tests/pcs/fixtures/labtrust-release"
    )
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _copy_schemas(root)
        bundle = json.loads(PF_SIGNED_BUNDLE.read_text(encoding="utf-8"))
        expected_claim_id = bundle["science_claim_bundle"]["claim_artifact"]["artifact_id"]
        result = import_signed_bundle(PF_SIGNED_BUNDLE, repo_root=root, write=True)
        assert result.claim_id == expected_claim_id
        read_model = json.loads(
            (root / "corpus" / "pcs" / "claims" / result.claim_id / "read_model.json").read_text(
                encoding="utf-8"
            )
        )
        assert read_model["verification_result"]["verification_id"].startswith("verification-")
        assert read_model["claim"]["signature_or_digest"].startswith("sha256:")


def test_import_labtrust_release_bundle_writes_corpus_artifacts() -> None:
    """Matches: just pcs-import-bundle tests/pcs/fixtures/labtrust-release/signed_science_claim_bundle.json"""
    assert LABTRUST_RELEASE_BUNDLE.is_file()
    bundle = json.loads(LABTRUST_RELEASE_BUNDLE.read_text(encoding="utf-8"))
    expected_claim_id = bundle["science_claim_bundle"]["claim_artifact"]["artifact_id"]
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _copy_schemas(root)
        result = import_signed_bundle(LABTRUST_RELEASE_BUNDLE, repo_root=root, write=True)
        assert result.claim_id == expected_claim_id
        claim_dir = root / "corpus" / "pcs" / "claims" / result.claim_id
        for name in (
            "signed_bundle.json",
            "read_model.json",
            "import_manifest.json",
            "scientific_memory_import_report.json",
        ):
            assert (claim_dir / name).is_file(), f"missing {name}"
        report = json.loads(
            (claim_dir / "scientific_memory_import_report.json").read_text(encoding="utf-8")
        )
        assert report["render_path"] == f"/pcs/claims/{result.claim_id}"
        assert report["verification_status"] == "passed"
        read_model = json.loads((claim_dir / "read_model.json").read_text(encoding="utf-8"))
        assert read_model["claim_id"] == expected_claim_id
        assert read_model["limitation_notice"]


def test_import_legacy_bundle_rejected_in_strict_mode() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _copy_schemas(root)
        with pytest.raises(BundleValidationError, match="--allow-legacy"):
            import_signed_bundle(
                LEGACY_SIGNED_BUNDLE, repo_root=root, strict=True, write=False
            )


def test_import_legacy_bundle_allowed_only_with_allow_legacy() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _copy_schemas(root)
        result = import_signed_bundle(
            LEGACY_SIGNED_BUNDLE,
            repo_root=root,
            strict=True,
            allow_legacy=True,
            write=True,
        )
        assert result.claim_id == "labtrust-qc-release-claim-001"


def test_import_missing_verification_result_rejected() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _copy_schemas(root)
        with pytest.raises(BundleValidationError, match="verification_result is required"):
            import_signed_bundle(
                FIXTURES / "missing_verification_result.json",
                repo_root=root,
                strict=True,
                allow_legacy=True,
                write=False,
            )


def test_import_missing_signature_or_digest_rejected() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _copy_schemas(root)
        with pytest.raises(BundleValidationError, match="signature_or_digest is required"):
            import_signed_bundle(
                FIXTURES / "labtrust-release" / "missing_claim_signature.json",
                repo_root=root,
                write=False,
            )


def test_import_rejects_placeholder_pf_source_commit() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _copy_schemas(root)
        with pytest.raises(BundleValidationError, match="placeholder commit"):
            import_signed_bundle(
                FIXTURES / "labtrust-release" / "invalid_placeholder_pf_source_commit.json",
                repo_root=root,
                write=False,
            )


def test_import_rejects_local_dev_in_release_fixture() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _copy_schemas(root)
        with pytest.raises(BundleValidationError, match="local_dev"):
            import_signed_bundle(
                FIXTURES / "labtrust-release" / "invalid_local_dev_release.json",
                repo_root=root,
                write=False,
            )


def test_import_accepts_pf_signed_bundle_with_real_commit() -> None:
    manifest = json.loads(LABTRUST_RELEASE_MANIFEST.read_text(encoding="utf-8"))
    bundle = json.loads(LABTRUST_RELEASE_BUNDLE.read_text(encoding="utf-8"))
    pf_commit = manifest["provability_fabric_commit"]
    assert bundle["verification_result"]["source_commit"] == pf_commit
    assert bundle["source_commit"] == pf_commit
    assert not is_placeholder_commit(pf_commit)
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _copy_schemas(root)
        result = import_signed_bundle(LABTRUST_RELEASE_BUNDLE, repo_root=root, write=True)
        assert result.claim_id == EXPECTED_LABTRUST_CLAIM_ID


def test_import_manifest_pf_provenance_alignment() -> None:
    manifest = json.loads(LABTRUST_RELEASE_MANIFEST.read_text(encoding="utf-8"))
    bundle = json.loads(LABTRUST_RELEASE_BUNDLE.read_text(encoding="utf-8"))
    pf_commit = manifest["provability_fabric_commit"]
    assert bundle["verification_result"]["source_commit"] == pf_commit
    assert bundle["source_commit"] == pf_commit


def test_import_missing_source_commit_rejected() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _copy_schemas(root)
        with pytest.raises(BundleValidationError, match="source_commit is required"):
            import_signed_bundle(
                FIXTURES / "labtrust-release" / "missing_claim_source_commit.json",
                repo_root=root,
                write=False,
            )


def test_import_failed_verification_result_rejected() -> None:
    failed = json.loads(
        (FIXTURES / "failed_pcs_core_verification_result.json").read_text(encoding="utf-8")
    )
    assert failed["verification_result"]["status"] == "failed"
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _copy_schemas(root)
        with pytest.raises(BundleValidationError, match="verification_result did not pass"):
            import_signed_bundle(
                FIXTURES / "failed_pcs_core_verification_result.json",
                repo_root=root,
                write=False,
            )


def test_import_report_contains_verification_status() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _copy_schemas(root)
        result = import_signed_bundle(PF_SIGNED_BUNDLE, repo_root=root, write=True)
        report = json.loads(
            (
                root
                / "corpus"
                / "pcs"
                / "claims"
                / result.claim_id
                / "scientific_memory_import_report.json"
            ).read_text(encoding="utf-8")
        )
        missing = IMPORT_REPORT_REQUIRED_KEYS - set(report.keys())
        assert not missing, f"import report missing keys: {sorted(missing)}"
        assert report["verification_status"] == "passed"
        assert report["claim_id"] == result.claim_id
        assert report["render_path"] == f"/pcs/claims/{result.claim_id}"
        assert isinstance(report["warnings"], list)
        assert isinstance(report["stale_artifacts"], list)


def _copy_schemas(root: Path) -> None:
    copy_pcs_schemas(root)
