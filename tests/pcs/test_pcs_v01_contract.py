"""LabTrust PCS v0.1 release contract manifest."""

from __future__ import annotations

import importlib
import json

import pytest

from sm_pipeline.pcs_validate.bundle_detection import detect_bundle_shape, is_pcs_core_signed_bundle

from schema_fixtures import PF_SIGNED_BUNDLE

REQUIRED_TEST_MODULES = (
    "test_pcs_import",
    "test_pcs_render",
    "test_labtrust_release_fixture",
    "test_release_chain_identity",
)

REQUIRED_TEST_NAMES = (
    "test_import_pf_signed_bundle_valid",
    "test_import_labtrust_release_bundle_writes_corpus_artifacts",
    "test_import_legacy_bundle_rejected_in_strict_mode",
    "test_import_legacy_bundle_allowed_only_with_allow_legacy",
    "test_import_missing_verification_result_rejected",
    "test_import_failed_verification_result_rejected",
    "test_import_missing_signature_or_digest_rejected",
    "test_import_missing_source_commit_rejected",
    "test_import_rejects_placeholder_pf_source_commit",
    "test_import_rejects_local_dev_in_release_fixture",
    "test_import_accepts_pf_signed_bundle_with_real_commit",
    "test_import_manifest_pf_provenance_alignment",
    "test_import_report_contains_verification_status",
    "test_render_claim_displays_runtime_receipt",
    "test_render_claim_displays_trace_certificate",
    "test_render_claim_displays_verification_result",
    "test_render_claim_displays_artifact_hashes",
    "test_render_claim_displays_source_repo_and_source_commit",
    "test_render_claim_displays_limitation_notice",
    "test_render_claim_read_model_matches_committed_fixture",
    "test_labtrust_release_fixture_manifest_is_current",
    "test_labtrust_release_pf_provenance_matches_release_manifest",
    "test_import_read_model_matches_canonical_golden_fixture",
    "test_pcs_corpus_claim_passes_validate_all_gate",
    "test_fixture_release_chain_identity",
    "test_render_read_model_certificate_matches_certified_bundle",
)


def test_pcs_v01_required_tests_are_defined() -> None:
    modules = [importlib.import_module(name) for name in REQUIRED_TEST_MODULES]
    for test_name in REQUIRED_TEST_NAMES:
        if not any(hasattr(mod, test_name) for mod in modules):
            pytest.fail(f"missing required test {test_name}")


def test_pf_canonical_fixture_is_pcs_core_signed_bundle() -> None:
    assert PF_SIGNED_BUNDLE.is_file(), "run: just refresh-pcs-fixtures"
    bundle = json.loads(PF_SIGNED_BUNDLE.read_text(encoding="utf-8"))
    assert is_pcs_core_signed_bundle(bundle)
    assert detect_bundle_shape(bundle) == "pcs_core"
    vr = bundle.get("verification_result")
    assert isinstance(vr, dict)
    assert vr.get("status") not in ("failed", "fail", "rejected")
