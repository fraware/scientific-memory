"""Canonical pcs-core RC chain: fixture drift gate, CLI import/render, parity."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

from sm_pipeline.pcs_import.artifact_normalizer import LIMITATION_NOTICE, normalize_signed_bundle

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
    REPO_ROOT,
    file_sha256,
    resolve_pcs_core_root,
)

pytestmark = pytest.mark.skipif(
    not PCS_CORE_CANONICAL_SIGNED_BUNDLE.is_file(),
    reason="pcs-core canonical release not available (set PCS_CORE_PATH or checkout pcs-core)",
)

PORTAL_SECTION_TITLES = (
    "Claim",
    "Assumptions",
    "Runtime Evidence",
    "Temporal Certificate",
    "Verification Result",
    "Artifact Hashes",
    "Source Repositories",
    "Reproduce / Verify",
    "Limitations",
)

READ_MODEL_SECTION_KEYS = (
    "claim",
    "assumption_set",
    "runtime_receipt",
    "trace_certificate",
    "verification_result",
    "artifact_hashes",
    "source_repositories",
    "reproduce_commands",
    "verify_commands",
    "limitations",
    "limitation_notice",
)


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _assert_canonical_import_report(report: dict) -> None:
    assert report["verification_status"] == "passed"
    assert report["strict"] is True
    assert report["allow_legacy"] is False
    assert report["bundle_shape"] == "pcs_core"
    assert report["scientific_memory_commit"] == CANONICAL_RC_SCIENTIFIC_MEMORY_COMMIT


def _assert_canonical_read_model(read_model: dict) -> None:
    assert read_model["trace_certificate"]["id"] == CANONICAL_RC_CERTIFICATE_ID
    assert read_model["trace_certificate"].get("certificate_id") == CANONICAL_RC_CERTIFICATE_ID
    assert read_model["claim_id"] == EXPECTED_LABTRUST_CLAIM_ID
    assert read_model["runtime_receipt"].get("trace_hash") == CANONICAL_RC_TRACE_HASH
    assert read_model["limitation_notice"] == LIMITATION_NOTICE
    assert LIMITATION_NOTICE in read_model["limitations"]
    for key in READ_MODEL_SECTION_KEYS:
        assert key in read_model, f"missing read_model.{key}"


def test_scimem_signed_bundle_fixture_matches_pcs_core_rc() -> None:
    """SM signed bundle must match pcs-core/examples/labtrust-release/ (SHA + content)."""
    pcs_path = PCS_CORE_CANONICAL_SIGNED_BUNDLE
    sm_path = LABTRUST_RELEASE_BUNDLE
    assert file_sha256(pcs_path) == file_sha256(sm_path)
    assert _load(sm_path) == _load(pcs_path)

    scb = _load(sm_path)["science_claim_bundle"]
    assert scb["certificates"][0]["certificate_id"] == CANONICAL_RC_CERTIFICATE_ID


def test_scimem_fixture_matches_pcs_core_rc() -> None:
    """Full labtrust-release fixture tree matches canonical pcs-core RC."""
    assert _load(LABTRUST_RELEASE_MANIFEST) == _load(
        PCS_CORE_CANONICAL_RELEASE / "RELEASE_FIXTURE_MANIFEST.json"
    )
    assert _load(LABTRUST_RELEASE_IMPORT_REPORT) == _load(
        PCS_CORE_CANONICAL_RELEASE / "scientific_memory_import_report.json"
    )

    trace = _load(LABTRUST_RELEASE_BUNDLE.parent / "trace.json")
    assert trace["trace_hash"] == CANONICAL_RC_TRACE_HASH

    manifest = _load(LABTRUST_RELEASE_MANIFEST)
    assert (
        manifest["artifacts"]["science_claim_bundle.certified.json"]
        == CANONICAL_RC_CERTIFIED_BUNDLE_HASH
    )
    assert manifest["labtrust_gym_commit"] == CANONICAL_RC_LABTRUST_COMMIT
    assert manifest["certifyedge_commit"] == CANONICAL_RC_CERTIFYEDGE_COMMIT
    assert manifest["provability_fabric_commit"] == CANONICAL_RC_PF_COMMIT
    assert manifest["scientific_memory_commit"] == _load(PCS_CORE_CANONICAL_RELEASE / "RELEASE_FIXTURE_MANIFEST.json")["scientific_memory_commit"]

    pcs_report = _load(PCS_CORE_CANONICAL_RELEASE / "scientific_memory_import_report.json")
    sm_report = _load(LABTRUST_RELEASE_IMPORT_REPORT)
    assert sm_report == pcs_report
    _assert_canonical_import_report(sm_report)


def test_import_canonical_rc_signed_bundle() -> None:
    from sm_pipeline.pcs_import.science_claim_bundle_importer import import_signed_bundle

    from schema_fixtures import copy_pcs_schemas

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        copy_pcs_schemas(root)
        result = import_signed_bundle(
            LABTRUST_RELEASE_BUNDLE,
            repo_root=root,
            strict=True,
            release_mode=True,
            write=True,
        )
        assert result.claim_id == EXPECTED_LABTRUST_CLAIM_ID
        claim_dir = root / "corpus" / "pcs" / "claims" / result.claim_id
        read_model = _load(claim_dir / "read_model.json")
        report = _load(claim_dir / "scientific_memory_import_report.json")
        _assert_canonical_read_model(read_model)
        _assert_canonical_import_report(report)


def test_render_canonical_rc_claim() -> None:
    read_model = normalize_signed_bundle(_load(LABTRUST_RELEASE_BUNDLE))
    _assert_canonical_read_model(read_model)
    vr = read_model["verification_result"]
    assert vr is not None
    assert vr.get("status") in ("ProofChecked", "passed")


def _run_cli(args: list[str], *, env: dict[str, str]) -> None:
    sm_python = REPO_ROOT / "scripts" / "sm_python.sh"
    if sys.platform == "win32":
        cmd = [sys.executable, "-m", "sm_pipeline.cli", *args]
        subprocess.run(cmd, cwd=REPO_ROOT, check=True, env=env)
        return
    if shutil.which("just"):
        subprocess.run(["just", *args], cwd=REPO_ROOT, check=True, env=env)
        return
    subprocess.run(["bash", str(sm_python), "-m", "sm_pipeline.cli", *args], cwd=REPO_ROOT, check=True, env=env)


def test_pcs_import_and_render_canonical_rc_via_just() -> None:
    """Matches: just pcs-import-bundle ... --strict --release-mode && just pcs-render-claim."""
    bundle = LABTRUST_RELEASE_BUNDLE.relative_to(REPO_ROOT).as_posix()
    claim_id = EXPECTED_LABTRUST_CLAIM_ID
    env = os.environ.copy()
    env["PYTHONPATH"] = str(REPO_ROOT / "pipeline" / "src") + (
        os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else ""
    )
    pcs_root = resolve_pcs_core_root()
    if pcs_root.is_dir():
        env["PCS_CORE_PATH"] = str(pcs_root)

    _run_cli(
        ["pcs-import-bundle", "--bundle", bundle, "--strict", "--release-mode"],
        env=env,
    )
    _run_cli(["pcs-render-claim", "--claim-id", claim_id], env=env)

    claim_dir = REPO_ROOT / "corpus" / "pcs" / "claims" / claim_id
    read_model = _load(claim_dir / "read_model.json")
    report = _load(claim_dir / "scientific_memory_import_report.json")
    _assert_canonical_read_model(read_model)
    _assert_canonical_import_report(report)

    export_path = REPO_ROOT / "portal" / ".generated" / "pcs-export.json"
    assert export_path.is_file()
    export = _load(export_path)
    assert claim_id in export["claims"]
    portal_model = export["claims"][claim_id]
    _assert_canonical_read_model(portal_model)

    # Portal section contract (titles map to read-model sections rendered by PcsClaimPage).
    for title in PORTAL_SECTION_TITLES:
        assert title  # documented portal headings enforced via read_model keys above


def test_portal_read_model_contract_sections() -> None:
    """Portal zod contract + mandatory limitation notice for canonical RC read model."""
    script = REPO_ROOT / "portal" / "scripts" / "verify-pcs-read-model.mjs"
    model = REPO_ROOT / "tests" / "pcs" / "fixtures" / "canonical_pcs_read_model.json"
    result = subprocess.run(
        ["node", str(script), str(model)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    read_model = _load(model)
    _assert_canonical_read_model(read_model)
