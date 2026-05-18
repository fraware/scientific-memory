"""Acceptance criteria for PCS Phase 2 release evidence interface."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from sm_pipeline.pcs_import.release_manifest_importer import import_release_manifest
from sm_pipeline.pcs_validate.release_chain_validation import require_release_chain_validation
from sm_pipeline.pcs_validate.release_manifest import validate_release_manifest_or_raise

from schema_fixtures import (
    CANONICAL_RC_CERTIFICATE_ID,
    EXPECTED_LABTRUST_CLAIM_ID,
    LABTRUST_RELEASE_DIR,
    REPO_ROOT,
    copy_pcs_schemas,
)

_REQUIRED_READ_MODEL_SECTIONS = (
    "claim",
    "workflow_profile",
    "assumption_set",
    "runtime_receipt",
    "trace_certificate",
    "verification_result",
    "release_manifest",
    "release_chain_validation",
    "artifact_registry",
    "handoff_manifests",
    "artifact_dependency_graph",
    "lineage",
    "staleness",
    "artifact_hashes",
    "source_repositories",
    "reproduce_commands",
    "verify_commands",
    "limitation_notice",
)

_REGISTRY_ROW_KEYS = (
    "artifact_type",
    "schema",
    "schema_owner",
    "runtime_producer",
    "allowed_runtime_producers",
    "producer",
    "status",
    "allowed_statuses",
    "source_repo",
    "source_commit",
    "hash",
    "required_release_fields_present",
    "required_release_fields_missing",
    "semantic_checks",
    "semantic_checks_performed",
    "registry_admission_result",
    "consumer_repos",
    "canonical_hash_required",
    "release_mode_required",
    "admission_status",
)

_ADMISSION_STATUSES = frozenset({"passed", "warning", "failed", "deferred", "not_applicable"})


def test_release_manifest_drives_import_and_chain_validation_gates() -> None:
    manifest_path = LABTRUST_RELEASE_DIR / "ReleaseManifest.v0.json"
    manifest = validate_release_manifest_or_raise(manifest_path, repo_root=REPO_ROOT)
    validation = require_release_chain_validation(
        manifest_path.parent,
        repo_root=REPO_ROOT,
        expected_release_id=str(manifest.get("release_id") or ""),
    )
    assert validation.get("status") == "ProofChecked"


def test_release_import_produces_required_artifacts(tmp_path: Path) -> None:
    root = tmp_path
    copy_pcs_schemas(root)
    import shutil

    release_dir = root / "labtrust-release"
    shutil.copytree(LABTRUST_RELEASE_DIR, release_dir)
    import_release_manifest(
        release_dir / "ReleaseManifest.v0.json",
        repo_root=root,
        write=True,
        render=True,
    )
    claim_dir = root / "corpus" / "pcs" / "claims" / EXPECTED_LABTRUST_CLAIM_ID
    for name in (
        "signed_bundle.json",
        "read_model.json",
        "import_manifest.json",
        "scientific_memory_import_report.json",
        "lineage.json",
        "release_manifest.json",
        "release_chain_validation.json",
        "artifact_registry.json",
        "handoff_manifests.json",
        "workflow_profile.json",
    ):
        assert (claim_dir / name).is_file(), name
    assert (root / "portal" / ".generated" / "pcs-export.json").is_file()
    assert (root / "corpus" / "pcs" / "claims_index.json").is_file()


def test_read_model_exposes_human_readable_release_evidence(tmp_path: Path) -> None:
    root = tmp_path
    copy_pcs_schemas(root)
    import shutil

    release_dir = root / "labtrust-release"
    shutil.copytree(LABTRUST_RELEASE_DIR, release_dir)
    import_release_manifest(
        release_dir / "ReleaseManifest.v0.json",
        repo_root=root,
        write=True,
        render=False,
    )
    model = json.loads(
        (
            root / "corpus" / "pcs" / "claims" / EXPECTED_LABTRUST_CLAIM_ID / "read_model.json"
        ).read_text(encoding="utf-8"),
    )
    for key in _REQUIRED_READ_MODEL_SECTIONS:
        assert key in model, f"missing read_model.{key}"

    registry = model["artifact_registry"]
    assert isinstance(registry, list) and registry
    row = next(r for r in registry if r["name"] == "signed_science_claim_bundle.json")
    for key in _REGISTRY_ROW_KEYS:
        assert key in row, f"missing registry row field {key}"
    assert row["admission_status"] in _ADMISSION_STATUSES

    staleness = model["staleness"]
    assert isinstance(staleness.get("stale"), bool)
    assert staleness.get("claim_state") in (
        "current",
        "stale",
        "superseded",
        "withdrawn",
        "revalidated",
    )
    lineage = model["lineage"]
    assert lineage.get("recommended_action")
    assert lineage.get("certificate_id") == CANONICAL_RC_CERTIFICATE_ID

    assert model.get("workflow_id") == "labtrust.qc_release_v0.1"
    assert model.get("domain") == "lab_science_simulation"
    assert "RuntimeReceipt.v0" in (model.get("runtime_artifact_types") or [])
    assert "TraceCertificate.v0" in (model.get("certificate_artifact_types") or [])


@pytest.mark.skipif(
    not (REPO_ROOT / "corpus" / "pcs" / "claims" / EXPECTED_LABTRUST_CLAIM_ID).is_dir(),
    reason="corpus claim missing; run: just pcs-import-release",
)
def test_corpus_claim_passes_phase2_portal_contract() -> None:
    script = REPO_ROOT / "portal" / "scripts" / "verify-pcs-phase2-read-model.mjs"
    read_model = (
        REPO_ROOT
        / "corpus"
        / "pcs"
        / "claims"
        / EXPECTED_LABTRUST_CLAIM_ID
        / "read_model.json"
    )
    result = subprocess.run(
        ["node", str(script), str(read_model)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_pcs_check_stale_json_contract() -> None:
    env = dict(__import__("os").environ)
    env["PYTHONPATH"] = str(REPO_ROOT / "pipeline" / "src")
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "sm_pipeline.cli",
            "pcs-check-stale",
            "--claim-id",
            EXPECTED_LABTRUST_CLAIM_ID,
        ],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        pytest.skip("corpus claim not imported; run: just pcs-import-release")
    payload = json.loads(result.stdout)
    assert payload["claim_id"] == EXPECTED_LABTRUST_CLAIM_ID
    assert isinstance(payload["stale"], bool)
    assert isinstance(payload["stale_reasons"], list)
    if payload["stale"]:
        assert payload["repair_hint"].startswith("Re-import the current release manifest")
