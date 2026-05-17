"""Canonical pcs-core RC chain: fixture parity, import, and render."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from sm_pipeline.pcs_import.artifact_normalizer import normalize_signed_bundle
from sm_pipeline.pcs_import.science_claim_bundle_importer import import_signed_bundle

from schema_fixtures import (
    CANONICAL_RC_CERTIFICATE_ID,
    CANONICAL_RC_CERTIFIED_BUNDLE_HASH,
    CANONICAL_RC_CERTIFYEDGE_COMMIT,
    CANONICAL_RC_LABTRUST_COMMIT,
    CANONICAL_RC_PF_COMMIT,
    CANONICAL_RC_SCIENTIFIC_MEMORY_COMMIT,
    CANONICAL_RC_TRACE_HASH,
    EXPECTED_LABTRUST_CLAIM_ID,
    LABTRUST_RELEASE_BUNDLE,
    LABTRUST_RELEASE_IMPORT_REPORT,
    LABTRUST_RELEASE_MANIFEST,
    PCS_CORE_CANONICAL_RELEASE,
    PCS_CORE_CANONICAL_SIGNED_BUNDLE,
    copy_pcs_schemas,
)

pytestmark = pytest.mark.skipif(
    not PCS_CORE_CANONICAL_SIGNED_BUNDLE.is_file(),
    reason="pcs-core canonical release not available at ../pcs-core/examples/labtrust-release",
)


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def test_scimem_fixture_matches_pcs_core_rc() -> None:
    """SM labtrust-release fixtures must match pcs-core/examples/labtrust-release/."""
    pcs_signed = _load(PCS_CORE_CANONICAL_SIGNED_BUNDLE)
    sm_signed = _load(LABTRUST_RELEASE_BUNDLE)
    assert sm_signed == pcs_signed

    pcs_manifest = _load(PCS_CORE_CANONICAL_RELEASE / "RELEASE_FIXTURE_MANIFEST.json")
    sm_manifest = _load(LABTRUST_RELEASE_MANIFEST)
    assert sm_manifest == pcs_manifest

    scb = sm_signed["science_claim_bundle"]
    assert scb["certificates"][0]["certificate_id"] == CANONICAL_RC_CERTIFICATE_ID

    trace = _load(LABTRUST_RELEASE_BUNDLE.parent / "trace.json")
    assert trace["trace_hash"] == CANONICAL_RC_TRACE_HASH

    manifest = sm_manifest
    assert manifest["artifacts"]["science_claim_bundle.certified.json"] == CANONICAL_RC_CERTIFIED_BUNDLE_HASH
    assert manifest["labtrust_gym_commit"] == CANONICAL_RC_LABTRUST_COMMIT
    assert manifest["certifyedge_commit"] == CANONICAL_RC_CERTIFYEDGE_COMMIT
    assert manifest["provability_fabric_commit"] == CANONICAL_RC_PF_COMMIT
    assert manifest["scientific_memory_commit"] == CANONICAL_RC_SCIENTIFIC_MEMORY_COMMIT

    report = _load(LABTRUST_RELEASE_IMPORT_REPORT)
    assert report["verification_status"] == "passed"
    assert report["strict"] is True
    assert report["allow_legacy"] is False
    assert report["bundle_shape"] == "pcs_core"
    assert report["scientific_memory_commit"] == CANONICAL_RC_SCIENTIFIC_MEMORY_COMMIT


def test_import_canonical_rc_signed_bundle() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        copy_pcs_schemas(root)
        result = import_signed_bundle(LABTRUST_RELEASE_BUNDLE, repo_root=root, write=True)
        assert result.claim_id == EXPECTED_LABTRUST_CLAIM_ID

        read_model = _load(
            root / "corpus" / "pcs" / "claims" / result.claim_id / "read_model.json"
        )
        assert read_model["trace_certificate"]["certificate_id"] == CANONICAL_RC_CERTIFICATE_ID
        assert read_model["trace_certificate"]["id"] == CANONICAL_RC_CERTIFICATE_ID

        report = _load(
            root / "corpus" / "pcs" / "claims" / result.claim_id / "scientific_memory_import_report.json"
        )
        assert report["verification_status"] == "passed"
        assert report["strict"] is True
        assert report["allow_legacy"] is False
        assert report["bundle_shape"] == "pcs_core"


def test_render_canonical_rc_claim() -> None:
    read_model = normalize_signed_bundle(_load(LABTRUST_RELEASE_BUNDLE))
    assert read_model["trace_certificate"]["id"] == CANONICAL_RC_CERTIFICATE_ID
    assert read_model["trace_certificate"]["certificate_id"] == CANONICAL_RC_CERTIFICATE_ID
    assert read_model["claim_id"] == EXPECTED_LABTRUST_CLAIM_ID
    vr = read_model["verification_result"]
    assert vr is not None
    assert vr.get("status") in ("ProofChecked", "passed")
