"""Canonical pcs-core RC gate: fixture drift, strict CLI import, render."""

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

# Portal headings (PcsClaimPage) mapped to read-model keys used for rendering.
PORTAL_SECTIONS: tuple[tuple[str, str], ...] = (
    ("Claim", "claim"),
    ("Assumptions", "assumption_set"),
    ("Runtime Evidence", "runtime_receipt"),
    ("Temporal Certificate", "trace_certificate"),
    ("Verification Result", "verification_result"),
    ("Artifact Hashes", "artifact_hashes"),
    ("Source Repositories", "source_repositories"),
    ("Reproduce / Verify", "reproduce_commands"),
    ("Limitations", "limitation_notice"),
)

PORTAL_SECTIONS_PHASE2: tuple[tuple[str, str], ...] = (
    ("Release Manifest", "release_manifest"),
    ("Release Chain Validation", "release_chain_validation"),
    ("Artifact Registry", "artifact_registry"),
)

PHASE2_READ_MODEL_KEYS = (
    "release_manifest",
    "release_chain_validation",
    "artifact_registry",
    "artifact_dependency_graph",
    "release_manifest_hash",
    "signed_bundle_hash",
)

READ_MODEL_SECTION_KEYS = tuple(
    {key for _, key in PORTAL_SECTIONS}
    | {key for _, key in PORTAL_SECTIONS_PHASE2}
    | {"verify_commands", "limitations", "artifact_dependency_graph"},
)


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _cli_env() -> dict[str, str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(REPO_ROOT / "pipeline" / "src") + (
        os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else ""
    )
    pcs_root = resolve_pcs_core_root()
    if pcs_root.is_dir():
        env["PCS_CORE_PATH"] = str(pcs_root)
    return env


def _run_pcs_import_release(*, env: dict[str, str]) -> None:
    manifest = (
        LABTRUST_RELEASE_BUNDLE.parent / "ReleaseManifest.v0.json"
    ).relative_to(REPO_ROOT).as_posix()
    if shutil.which("just") and sys.platform != "win32":
        subprocess.run(
            ["just", "pcs-import-release", f"release_manifest={manifest}"],
            cwd=REPO_ROOT,
            check=True,
            env=env,
        )
        return
    subprocess.run(
        [
            sys.executable,
            "-m",
            "sm_pipeline.cli",
            "pcs-import-release",
            "--release-manifest",
            manifest,
        ],
        cwd=REPO_ROOT,
        check=True,
        env=env,
    )


def _run_pcs_import_bundle(*, env: dict[str, str]) -> None:
    bundle = LABTRUST_RELEASE_BUNDLE.relative_to(REPO_ROOT).as_posix()
    if shutil.which("just") and sys.platform != "win32":
        subprocess.run(
            ["just", "pcs-import-bundle", bundle, "--strict", "--release-mode"],
            cwd=REPO_ROOT,
            check=True,
            env=env,
        )
        return
    subprocess.run(
        [
            sys.executable,
            "-m",
            "sm_pipeline.cli",
            "pcs-import-bundle",
            "--bundle",
            bundle,
            "--strict",
            "--release-mode",
        ],
        cwd=REPO_ROOT,
        check=True,
        env=env,
    )


def _run_pcs_render_claim(*, env: dict[str, str]) -> None:
    claim_id = EXPECTED_LABTRUST_CLAIM_ID
    if shutil.which("just") and sys.platform != "win32":
        subprocess.run(
            ["just", "pcs-render-claim", claim_id],
            cwd=REPO_ROOT,
            check=True,
            env=env,
        )
        return
    subprocess.run(
        [
            sys.executable,
            "-m",
            "sm_pipeline.cli",
            "pcs-render-claim",
            "--claim-id",
            claim_id,
        ],
        cwd=REPO_ROOT,
        check=True,
        env=env,
    )


def _assert_canonical_import_report(report: dict, *, pinned_sm_commit: bool = True) -> None:
    assert report["verification_status"] == "passed"
    assert report["strict"] is True
    assert report["allow_legacy"] is False
    assert report["bundle_shape"] == "pcs_core"
    sm_commit = report.get("scientific_memory_commit", "")
    if pinned_sm_commit:
        assert sm_commit == CANONICAL_RC_SCIENTIFIC_MEMORY_COMMIT
    else:
        assert isinstance(sm_commit, str) and len(sm_commit) == 40 and sm_commit != "0" * 40


def _assert_phase2_import_report(report: dict) -> None:
    _assert_canonical_import_report(report, pinned_sm_commit=False)
    assert report.get("release_id") == "release-pcs-v0.1-labtrust-qc"
    assert report.get("release_chain_validation_status") == "ProofChecked"
    assert str(report.get("release_manifest_hash", "")).startswith("sha256:")


def _assert_canonical_rc_identity(*, report: dict, read_model: dict) -> None:
    _assert_canonical_import_report(report)
    _assert_canonical_read_model(read_model)
    if read_model.get("release_manifest"):
        _assert_phase2_read_model(read_model)
    if report.get("release_chain_validation_status"):
        assert report["release_chain_validation_status"] == "ProofChecked"


def _assert_phase2_read_model(read_model: dict) -> None:
    for _title, key in PORTAL_SECTIONS_PHASE2:
        assert key in read_model, f"missing read_model.{key}"
    for key in PHASE2_READ_MODEL_KEYS:
        assert key in read_model, f"missing read_model.{key}"
    assert read_model["release_chain_validation"]["status"] == "ProofChecked"
    assert read_model["release_manifest"]["release_id"] == "release-pcs-v0.1-labtrust-qc"
    assert len(read_model["artifact_registry"]) >= 8
    assert len(read_model["artifact_dependency_graph"]) >= 2


def _assert_canonical_read_model(read_model: dict) -> None:
    assert read_model["trace_certificate"]["id"] == CANONICAL_RC_CERTIFICATE_ID
    assert read_model["trace_certificate"].get("certificate_id") == CANONICAL_RC_CERTIFICATE_ID
    assert read_model["claim_id"] == EXPECTED_LABTRUST_CLAIM_ID
    assert read_model["runtime_receipt"].get("trace_hash") == CANONICAL_RC_TRACE_HASH
    assert read_model["limitation_notice"] == LIMITATION_NOTICE
    assert LIMITATION_NOTICE in read_model["limitations"]
    for _title, key in PORTAL_SECTIONS:
        assert key in read_model, f"missing read_model.{key}"
    assert read_model.get("verify_commands") is not None


def test_scimem_signed_bundle_fixture_matches_pcs_core_rc() -> None:
    """Byte-identical signed bundle vs $PCS_CORE_PATH/examples/labtrust-release/."""
    pcs_path = PCS_CORE_CANONICAL_SIGNED_BUNDLE
    sm_path = LABTRUST_RELEASE_BUNDLE
    assert pcs_path.read_bytes() == sm_path.read_bytes(), "signed bundle byte mismatch"
    assert file_sha256(pcs_path) == file_sha256(sm_path)
    assert _load(sm_path) == _load(pcs_path)
    scb = _load(sm_path)["science_claim_bundle"]
    assert scb["certificates"][0]["certificate_id"] == CANONICAL_RC_CERTIFICATE_ID


def test_scimem_fixture_matches_pcs_core_rc() -> None:
    """Manifest chain + import report aligned with pcs-core RC (SM commit pinned separately)."""
    sm_manifest = _load(LABTRUST_RELEASE_MANIFEST)
    pcs_manifest = _load(PCS_CORE_CANONICAL_RELEASE / "RELEASE_FIXTURE_MANIFEST.json")
    # SM-owned import report may differ when scientific_memory_commit is RC-pinned locally.
    sm_artifacts = {
        k: v for k, v in sm_manifest["artifacts"].items()
        if k != "scientific_memory_import_report.json"
    }
    pcs_artifacts = {
        k: v for k, v in pcs_manifest["artifacts"].items()
        if k != "scientific_memory_import_report.json"
    }
    assert sm_artifacts == pcs_artifacts
    for key in ("labtrust_gym_commit", "certifyedge_commit", "provability_fabric_commit"):
        assert sm_manifest[key] == pcs_manifest[key]
    assert sm_manifest["scientific_memory_commit"] == CANONICAL_RC_SCIENTIFIC_MEMORY_COMMIT

    sm_report = _load(LABTRUST_RELEASE_IMPORT_REPORT)
    assert sm_report["scientific_memory_commit"] == CANONICAL_RC_SCIENTIFIC_MEMORY_COMMIT
    assert sm_report["source_commit"] == CANONICAL_RC_SCIENTIFIC_MEMORY_COMMIT
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
    assert manifest["scientific_memory_commit"] == CANONICAL_RC_SCIENTIFIC_MEMORY_COMMIT
    _assert_canonical_import_report(_load(LABTRUST_RELEASE_IMPORT_REPORT))


def test_scimem_import_via_release_manifest() -> None:
    """just pcs-import-release (Phase 2 primary import path)."""
    env = _cli_env()
    _run_pcs_import_release(env=env)
    claim_dir = REPO_ROOT / "corpus" / "pcs" / "claims" / EXPECTED_LABTRUST_CLAIM_ID
    read_model = _load(claim_dir / "read_model.json")
    report = _load(claim_dir / "scientific_memory_import_report.json")
    _assert_phase2_import_report(report)
    _assert_canonical_read_model(read_model)
    _assert_phase2_read_model(read_model)
    assert (claim_dir / "lineage.json").is_file()


def test_scimem_strict_import_canonical_rc_bundle() -> None:
    """just pcs-import-bundle <fixture> --strict --release-mode (RC strict import gate)."""
    env = _cli_env()
    _run_pcs_import_bundle(env=env)
    claim_dir = REPO_ROOT / "corpus" / "pcs" / "claims" / EXPECTED_LABTRUST_CLAIM_ID
    read_model = _load(claim_dir / "read_model.json")
    report = _load(claim_dir / "scientific_memory_import_report.json")
    _assert_canonical_rc_identity(report=report, read_model=read_model)


def test_scimem_render_canonical_rc_claim() -> None:
    """just pcs-render-claim claim-pcs-qc-release-v0.1 (portal export + read model gate)."""
    env = _cli_env()
    _run_pcs_import_bundle(env=env)
    _run_pcs_render_claim(env=env)

    claim_dir = REPO_ROOT / "corpus" / "pcs" / "claims" / EXPECTED_LABTRUST_CLAIM_ID
    read_model = _load(claim_dir / "read_model.json")
    _assert_canonical_read_model(read_model)

    export_path = REPO_ROOT / "portal" / ".generated" / "pcs-export.json"
    assert export_path.is_file()
    portal_model = _load(export_path)["claims"][EXPECTED_LABTRUST_CLAIM_ID]
    _assert_canonical_read_model(portal_model)


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
        _assert_canonical_rc_identity(
            report=_load(claim_dir / "scientific_memory_import_report.json"),
            read_model=_load(claim_dir / "read_model.json"),
        )


def test_render_canonical_rc_claim() -> None:
    read_model = normalize_signed_bundle(_load(LABTRUST_RELEASE_BUNDLE))
    _assert_canonical_read_model(read_model)


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
    _assert_canonical_read_model(_load(model))
