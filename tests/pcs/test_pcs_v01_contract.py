"""LabTrust PCS v0.1 contract manifest: required tests and fixture shape."""

from __future__ import annotations

import importlib
import json
from pathlib import Path

import pytest

from sm_pipeline.pcs_validate.bundle_detection import detect_bundle_shape, is_pcs_core_signed_bundle

from schema_fixtures import copy_pcs_schemas

FIXTURES = Path(__file__).resolve().parent / "fixtures"

REQUIRED_TEST_MODULES = (
    "test_pcs_import",
    "test_pcs_render",
)

REQUIRED_TEST_NAMES = (
    "test_import_pcs_core_signed_bundle_valid",
    "test_import_legacy_bundle_requires_allow_legacy_in_strict_mode",
    "test_import_rejects_failed_verification_result",
    "test_import_rejects_missing_verification_result_in_strict_mode",
    "test_import_report_contains_verification_status_and_render_path",
    "test_render_claim_displays_verification_result",
    "test_render_claim_displays_artifact_hashes",
    "test_render_claim_displays_limitation_notice",
    "test_render_claim_displays_source_repo_and_source_commit",
)


def test_pcs_v01_required_tests_are_defined() -> None:
    modules = [importlib.import_module(name) for name in REQUIRED_TEST_MODULES]
    for test_name in REQUIRED_TEST_NAMES:
        if not any(hasattr(mod, test_name) for mod in modules):
            pytest.fail(f"missing required test {test_name}")


def test_canonical_fixture_is_pcs_core_signed_bundle() -> None:
    bundle = json.loads(
        (FIXTURES / "signed_science_claim_bundle.json").read_text(encoding="utf-8")
    )
    assert is_pcs_core_signed_bundle(bundle)
    assert detect_bundle_shape(bundle) == "pcs_core"
    scb = bundle["science_claim_bundle"]
    assert scb.get("schema_version") == "v0"
    assert "claim_artifact" in scb
    assert bundle.get("signed_bundle_id")
    vr = bundle.get("verification_result")
    assert isinstance(vr, dict)
    assert vr.get("status") not in ("failed", "fail", "rejected")


def test_canonical_fixture_provenance_documents_source() -> None:
    path = FIXTURES / "canonical_fixture_provenance.json"
    assert path.is_file(), "run: just refresh-pcs-fixtures"
    prov = json.loads(path.read_text(encoding="utf-8"))
    assert prov.get("fixture") == "signed_science_claim_bundle.json"
    assert prov.get("bundle_shape") == "pcs_core"
