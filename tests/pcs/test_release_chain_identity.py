"""Release-run identity: certified bundle, signed bundle, manifest, read model."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

from sm_pipeline.pcs_import.artifact_normalizer import normalize_signed_bundle
from sm_pipeline.pcs_import.science_claim_bundle_importer import import_signed_bundle
from sm_pipeline.pcs_validate.release_chain import validate_release_chain

from schema_fixtures import (
    EXPECTED_LABTRUST_CLAIM_ID,
    LABTRUST_RELEASE_BUNDLE,
    LABTRUST_RELEASE_CERTIFIED,
    LABTRUST_RELEASE_IMPORT_REPORT,
    LABTRUST_RELEASE_MANIFEST,
    copy_pcs_schemas,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
RELEASE_RUN = REPO_ROOT / "release-run"
FIXTURES = Path(__file__).resolve().parent / "fixtures" / "labtrust-release"


def _first_certificate_id(bundle: dict) -> str:
    certs = bundle.get("certificates")
    assert isinstance(certs, list) and certs
    return str(certs[0]["certificate_id"])


def _vr_certificate_ref(vr: dict) -> str:
    for check in vr.get("checks") or []:
        if check.get("check_id") == "evidence_refs_complete":
            refs = (check.get("details") or {}).get("certificate_refs") or []
            assert refs
            return str(refs[0])
    pytest.fail("evidence_refs_complete check missing certificate_refs")


def test_release_run_directory_passes_chain_validation() -> None:
    if not RELEASE_RUN.is_dir():
        pytest.skip("release-run not populated; run: just refresh-pcs-release")
    issues = validate_release_chain(RELEASE_RUN)
    assert not issues, "\n".join(i.format() for i in issues)


def test_release_chain_consistency_import() -> None:
    """Release-chain consistency across manifest, certified bundle, signed bundle, import report."""
    manifest = json.loads(LABTRUST_RELEASE_MANIFEST.read_text(encoding="utf-8-sig"))
    certified = json.loads(LABTRUST_RELEASE_CERTIFIED.read_text(encoding="utf-8-sig"))
    signed = json.loads(LABTRUST_RELEASE_BUNDLE.read_text(encoding="utf-8-sig"))
    report = json.loads(LABTRUST_RELEASE_IMPORT_REPORT.read_text(encoding="utf-8-sig"))
    scb = signed["science_claim_bundle"]

    assert scb["bundle_id"] == certified["bundle_id"]
    assert _first_certificate_id(scb) == _first_certificate_id(certified)
    assert report["verification_status"] == "passed"
    assert report["scientific_memory_commit"] == manifest["scientific_memory_commit"]


def test_fixture_release_chain_identity() -> None:
    manifest = json.loads(LABTRUST_RELEASE_MANIFEST.read_text(encoding="utf-8-sig"))
    certified = json.loads(
        (FIXTURES / "science_claim_bundle.certified.json").read_text(encoding="utf-8-sig")
    )
    signed = json.loads(LABTRUST_RELEASE_BUNDLE.read_text(encoding="utf-8-sig"))
    report = json.loads(
        (FIXTURES / "scientific_memory_import_report.json").read_text(encoding="utf-8-sig")
    )
    scb = signed["science_claim_bundle"]
    vr = signed["verification_result"]

    assert scb["bundle_id"] == certified["bundle_id"]
    assert _first_certificate_id(certified) == _first_certificate_id(scb)
    assert _first_certificate_id(certified) == _vr_certificate_ref(vr)
    assert vr["status"] == "ProofChecked"
    assert report["verification_status"] == "passed"
    assert report.get("strict") is True
    assert report.get("allow_legacy") is False
    assert report.get("bundle_shape") == "pcs_core"
    assert vr["source_commit"] == manifest["provability_fabric_commit"]
    assert signed["source_commit"] == manifest["provability_fabric_commit"]


def test_render_read_model_certificate_matches_certified_bundle() -> None:
    certified = json.loads(
        (FIXTURES / "science_claim_bundle.certified.json").read_text(encoding="utf-8-sig")
    )
    expected_cert = _first_certificate_id(certified)
    read_model = normalize_signed_bundle(
        json.loads(LABTRUST_RELEASE_BUNDLE.read_text(encoding="utf-8-sig"))
    )
    assert read_model["trace_certificate"]["id"] == expected_cert
    assert read_model["claim_id"] == EXPECTED_LABTRUST_CLAIM_ID


def test_import_from_release_run_matches_certified_certificate_id() -> None:
    if not (RELEASE_RUN / "signed_science_claim_bundle.json").is_file():
        pytest.skip("release-run not populated")
    certified = json.loads(
        (RELEASE_RUN / "science_claim_bundle.certified.json").read_text(encoding="utf-8-sig")
    )
    expected_cert = _first_certificate_id(certified)
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        copy_pcs_schemas(root)
        result = import_signed_bundle(
            RELEASE_RUN / "signed_science_claim_bundle.json",
            repo_root=root,
            write=True,
        )
        read_model = json.loads(
            (root / "corpus" / "pcs" / "claims" / result.claim_id / "read_model.json").read_text(
                encoding="utf-8"
            )
        )
        assert read_model["trace_certificate"]["id"] == expected_cert


def test_promote_release_run_script_validates_release_run() -> None:
    if not (RELEASE_RUN / "signed_science_claim_bundle.json").is_file():
        pytest.skip("release-run not populated")
    script = REPO_ROOT / "scripts" / "promote_release_run.py"
    result = subprocess.run(
        [sys.executable, str(script), "--run-dir", str(RELEASE_RUN), "--target", str(FIXTURES)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
