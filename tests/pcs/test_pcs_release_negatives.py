"""Release-mode negative import tests for PCS v0.1 RC."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from sm_pipeline.pcs_import.science_claim_bundle_importer import import_signed_bundle
from sm_pipeline.pcs_validate.validator import BundleValidationError

from schema_fixtures import (
    LABTRUST_RELEASE_BUNDLE,
    LEGACY_SIGNED_BUNDLE,
    copy_pcs_schemas,
)

FIXTURES = Path(__file__).resolve().parent / "fixtures"


def _mutated_bundle(mutator) -> dict:
    bundle = json.loads(LABTRUST_RELEASE_BUNDLE.read_text(encoding="utf-8-sig"))
    mutator(bundle)
    return bundle


def test_import_rejects_legacy_bundle_in_release_mode() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        copy_pcs_schemas(root)
        with pytest.raises(BundleValidationError, match="--allow-legacy"):
            import_signed_bundle(
                LEGACY_SIGNED_BUNDLE,
                repo_root=root,
                strict=True,
                release_mode=True,
                write=False,
            )


def test_import_rejects_missing_verification_result() -> None:
    def tamper(bundle: dict) -> None:
        bundle.pop("verification_result", None)
        scb = bundle.get("science_claim_bundle")
        if isinstance(scb, dict):
            scb.pop("verification_result", None)

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        copy_pcs_schemas(root)
        path = root / "missing_verification_result.json"
        path.write_text(json.dumps(_mutated_bundle(tamper), indent=2) + "\n", encoding="utf-8")
        with pytest.raises(BundleValidationError, match="verification_result is required"):
            import_signed_bundle(
                path,
                repo_root=root,
                strict=True,
                release_mode=True,
                write=False,
            )


def test_import_rejects_failed_verification_result() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        copy_pcs_schemas(root)
        with pytest.raises(BundleValidationError, match="verification_result did not pass"):
            import_signed_bundle(
                FIXTURES / "failed_pcs_core_verification_result.json",
                repo_root=root,
                strict=True,
                release_mode=True,
                write=False,
            )


def test_import_rejects_tampered_certificate_id() -> None:
    def tamper(bundle: dict) -> None:
        bundle["science_claim_bundle"]["certificates"][0]["certificate_id"] = (
            "cert-trace-tampered-00000000-0000-0000-0000-000000000001"
        )

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        copy_pcs_schemas(root)
        path = root / "tampered_certificate.json"
        path.write_text(json.dumps(_mutated_bundle(tamper), indent=2) + "\n", encoding="utf-8")
        with pytest.raises(BundleValidationError, match="certificate_refs"):
            import_signed_bundle(
                path,
                repo_root=root,
                strict=True,
                release_mode=True,
                write=False,
            )


def test_import_rejects_tampered_trace_hash() -> None:
    def tamper(bundle: dict) -> None:
        bundle["science_claim_bundle"]["runtime_receipts"][0]["trace_hash"] = (
            "sha256:" + "0" * 64
        )

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        copy_pcs_schemas(root)
        path = root / "tampered_trace_hash.json"
        path.write_text(json.dumps(_mutated_bundle(tamper), indent=2) + "\n", encoding="utf-8")
        with pytest.raises(BundleValidationError, match="trace_hash mismatch"):
            import_signed_bundle(
                path,
                repo_root=root,
                strict=True,
                release_mode=True,
                write=False,
            )
