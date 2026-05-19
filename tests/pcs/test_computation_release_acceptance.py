"""Computation reproducibility release import and read-model acceptance."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from schema_fixtures import REPO_ROOT, copy_pcs_schemas, pcs_cli_env, pcs_subprocess_python

FIXTURE = REPO_ROOT / "tests" / "pcs" / "fixtures" / "computation-release"
REJECTED = REPO_ROOT / "tests" / "pcs" / "fixtures" / "computation-rejected-release"
VERIFY_SCRIPT = REPO_ROOT / "scripts" / "verify_computation_release_fixture.py"
CLAIM_ID = "claim-computation-release-v0.1"
WORKFLOW_ID = "scientific_computation.reproducibility_v0"


def test_verify_computation_release_fixture_script() -> None:
    import subprocess
    import sys

    assert VERIFY_SCRIPT.is_file()
    result = subprocess.run(
        [sys.executable, str(VERIFY_SCRIPT)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.fixture()
def temp_repo(tmp_path: Path) -> Path:
    copy_pcs_schemas(tmp_path)
    return tmp_path


def test_computation_import_promotes_protocol_artifacts(temp_repo: Path) -> None:
    import subprocess
    import sys

    manifest = FIXTURE / "release_manifest.v0.json"
    result = subprocess.run(
        [
            pcs_subprocess_python(),
            "-m",
            "sm_pipeline.cli",
            "pcs-import-release",
            "--release-manifest",
            str(manifest),
        ],
        cwd=REPO_ROOT,
        env=pcs_cli_env(repo_root=REPO_ROOT),
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr

    read_model = json.loads(
        (REPO_ROOT / "corpus" / "pcs" / "claims" / CLAIM_ID / "read_model.json").read_text(
            encoding="utf-8",
        ),
    )
    assert read_model["workflow_id"] == WORKFLOW_ID
    assert read_model["domain"] == "scientific_computation"
    assert read_model.get("dataset_receipt", {}).get("id") == "dataset-demo-measurements-v0.1"
    assert read_model.get("computation_witness", {}).get("payload", {}).get("status") == (
        "CertificateChecked"
    )
    assert "computational provenance" in read_model.get("limitation_notice", "")
    kernel = read_model.get("formal_trust_kernel")
    assert isinstance(kernel, dict)
    assert kernel.get("overall_status") == "ProofChecked"
    assert len(kernel.get("lean_check_results") or []) >= 5


def test_computation_rejected_witness_renders_failure_evidence() -> None:
    import subprocess

    manifest = REJECTED / "release_manifest.v0.json"
    result = subprocess.run(
        [
            pcs_subprocess_python(),
            "-m",
            "sm_pipeline.cli",
            "pcs-import-release",
            "--release-manifest",
            str(manifest),
        ],
        cwd=REPO_ROOT,
        env=pcs_cli_env(repo_root=REPO_ROOT),
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr

    read_model = json.loads(
        (
            REPO_ROOT
            / "corpus"
            / "pcs"
            / "claims"
            / "claim-computation-rejected-v0.1"
            / "read_model.json"
        ).read_text(encoding="utf-8"),
    )
    witness = read_model.get("computation_witness", {}).get("payload", {})
    assert witness.get("status") == "Rejected"
    violations = witness.get("violations") or []
    assert len(violations) >= 1
    assert violations[0].get("violation_type") == "result_hash_mismatch"
    assert violations[0].get("expected_hash", "").startswith("sha256:")
    assert violations[0].get("actual_hash", "").startswith("sha256:")
    assert violations[0].get("responsible_component")
    assert violations[0].get("explanation")
