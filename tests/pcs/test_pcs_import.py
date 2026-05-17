"""PCS import contract tests (canonical pcs-core shape is default in strict mode)."""

import json
import tempfile
from pathlib import Path

import pytest

from sm_pipeline.pcs_import.science_claim_bundle_importer import import_signed_bundle
from sm_pipeline.pcs_validate.schema_registry import (
    SIGNED_BUNDLE_SCHEMA,
    resolve_schema_path,
)
from sm_pipeline.pcs_validate.validator import BundleValidationError, validate_signed_bundle

from schema_fixtures import copy_pcs_schemas

FIXTURES = Path(__file__).resolve().parent / "fixtures"
REPO_ROOT = Path(__file__).resolve().parents[2]


def test_import_pcs_core_signed_bundle_valid() -> None:
    bundle_path = FIXTURES / "signed_science_claim_bundle.json"
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _copy_schemas(root)
        result = import_signed_bundle(bundle_path, repo_root=root, write=True)
        assert result.claim_id == "claim-qc-release-v0.1"
        read_model = json.loads(
            (root / "corpus" / "pcs" / "claims" / result.claim_id / "read_model.json").read_text(
                encoding="utf-8"
            )
        )
        vr = read_model["verification_result"]
        assert vr["verification_id"] == "verify-scb-qc-release-v0.1"
        assert vr["verifier"] == "provability-fabric"
        assert read_model["canonical_digests"]["signed_bundle"]
        claim = read_model["claim"]
        assert claim["signature_or_digest"].startswith("sha256:")


def test_import_legacy_bundle_requires_allow_legacy_in_strict_mode() -> None:
    bundle_path = FIXTURES / "valid_signed_science_claim_bundle.json"
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _copy_schemas(root)
        with pytest.raises(BundleValidationError, match="--allow-legacy"):
            import_signed_bundle(bundle_path, repo_root=root, strict=True, write=False)

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _copy_schemas(root)
        result = import_signed_bundle(
            bundle_path,
            repo_root=root,
            strict=True,
            allow_legacy=True,
            write=True,
        )
        assert result.claim_id == "labtrust-qc-release-claim-001"
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
        assert report["bundle_shape"] == "legacy"
        assert report["allow_legacy"] is True


def test_import_rejects_failed_verification_result() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _copy_schemas(root)
        with pytest.raises(BundleValidationError, match="verification_result did not pass"):
            import_signed_bundle(
                FIXTURES / "failed_pcs_core_verification_result.json",
                repo_root=root,
                write=False,
            )


def test_import_rejects_missing_verification_result_in_strict_mode() -> None:
    bundle_path = FIXTURES / "missing_verification_result.json"
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _copy_schemas(root)
        with pytest.raises(BundleValidationError, match="verification_result is required"):
            import_signed_bundle(
                bundle_path,
                repo_root=root,
                strict=True,
                allow_legacy=True,
                write=False,
            )


def test_import_report_contains_verification_status_and_render_path() -> None:
    bundle_path = FIXTURES / "signed_science_claim_bundle.json"
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _copy_schemas(root)
        result = import_signed_bundle(bundle_path, repo_root=root, write=True)
        report_path = (
            root
            / "corpus"
            / "pcs"
            / "claims"
            / result.claim_id
            / "scientific_memory_import_report.json"
        )
        assert report_path.is_file()
        report = json.loads(report_path.read_text(encoding="utf-8"))
        assert report["verification_status"] == "passed"
        assert report["render_path"] == f"/pcs/claims/{result.claim_id}"
        assert report["claim_id"] == result.claim_id
        assert report["bundle_shape"] == "pcs_core"
        assert report["strict"] is True
        assert report["allow_legacy"] is False
        assert "imported_at" in report
        assert "source_bundle_path" in report


def test_import_rejects_missing_assumption_set() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _copy_schemas(root)
        with pytest.raises(BundleValidationError):
            import_signed_bundle(
                FIXTURES / "missing_assumption_set.json",
                repo_root=root,
                strict=True,
                allow_legacy=True,
                write=False,
            )


def test_import_rejects_empty_assumptions() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _copy_schemas(root)
        with pytest.raises(BundleValidationError):
            import_signed_bundle(
                FIXTURES / "missing_assumptions.json",
                repo_root=root,
                strict=True,
                allow_legacy=True,
                write=False,
            )


def test_canonical_schema_files_exist() -> None:
    schemas_dir = REPO_ROOT / "schemas" / "pcs"
    assert resolve_schema_path(schemas_dir, SIGNED_BUNDLE_SCHEMA).name == SIGNED_BUNDLE_SCHEMA


def _copy_schemas(root: Path) -> None:
    copy_pcs_schemas(root)
