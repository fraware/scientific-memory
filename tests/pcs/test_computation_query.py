"""Computation-specific PCS index queries."""

from __future__ import annotations

import json
import subprocess

import pytest

from schema_fixtures import REPO_ROOT, pcs_cli_env, pcs_subprocess_python

FIXTURE = REPO_ROOT / "tests" / "pcs" / "fixtures" / "computation-release"


@pytest.fixture(scope="module", autouse=True)
def _import_computation_release() -> None:
    result = subprocess.run(
        [
            pcs_subprocess_python(),
            "-m",
            "sm_pipeline.cli",
            "pcs-import-release",
            "--release-manifest",
            str(FIXTURE / "release_manifest.v0.json"),
        ],
        cwd=REPO_ROOT,
        env=pcs_cli_env(repo_root=REPO_ROOT),
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_list_claims_by_dataset() -> None:
    result = subprocess.run(
        [
            pcs_subprocess_python(),
            "-m",
            "sm_pipeline.cli",
            "pcs-list-claims-by-dataset",
            "--dataset-id",
            "dataset-demo-measurements-v0.1",
        ],
        cwd=REPO_ROOT,
        env=pcs_cli_env(repo_root=REPO_ROOT),
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "claim-computation-release-v0.1" in result.stdout


def test_list_claims_by_code_commit() -> None:
    dataset = json.loads((FIXTURE / "dataset_receipt.json").read_text(encoding="utf-8"))
    run = json.loads((FIXTURE / "computation_run_receipt.json").read_text(encoding="utf-8"))
    assert dataset["dataset_id"]
    result = subprocess.run(
        [
            pcs_subprocess_python(),
            "-m",
            "sm_pipeline.cli",
            "pcs-list-claims-by-code-commit",
            "--commit",
            run["code_commit"],
        ],
        cwd=REPO_ROOT,
        env=pcs_cli_env(repo_root=REPO_ROOT),
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "claim-computation-release-v0.1" in result.stdout


def test_list_claims_by_result_hash() -> None:
    result_artifact = json.loads((FIXTURE / "result_artifact.json").read_text(encoding="utf-8"))
    result = subprocess.run(
        [
            pcs_subprocess_python(),
            "-m",
            "sm_pipeline.cli",
            "pcs-list-claims-by-result-hash",
            "--result-hash",
            result_artifact["sha256"],
        ],
        cwd=REPO_ROOT,
        env=pcs_cli_env(repo_root=REPO_ROOT),
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "claim-computation-release-v0.1" in result.stdout


def test_list_claims_by_environment() -> None:
    environment = json.loads((FIXTURE / "environment_receipt.json").read_text(encoding="utf-8"))
    result = subprocess.run(
        [
            pcs_subprocess_python(),
            "-m",
            "sm_pipeline.cli",
            "pcs-list-claims-by-environment",
            "--environment-id",
            environment["environment_id"],
        ],
        cwd=REPO_ROOT,
        env=pcs_cli_env(repo_root=REPO_ROOT),
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "claim-computation-release-v0.1" in result.stdout
