"""Computation release comparison via lineage."""

from __future__ import annotations

import json
import subprocess

import pytest

from schema_fixtures import REPO_ROOT, pcs_cli_env, pcs_subprocess_python

LABTRUST = "release-pcs-v0.1-labtrust-qc"
COMPUTATION = "release-pcs-v0.1-scientific-computation-reproducibility"


@pytest.fixture(scope="module", autouse=True)
def _import_releases() -> None:
    for manifest in (
        REPO_ROOT / "tests/pcs/fixtures/labtrust-release/ReleaseManifest.v0.json",
        REPO_ROOT / "tests/pcs/fixtures/computation-release/release_manifest.v0.json",
    ):
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


def test_compare_labtrust_to_computation_includes_computation_diff() -> None:
    result = subprocess.run(
        [
            pcs_subprocess_python(),
            "-m",
            "sm_pipeline.cli",
            "pcs-compare-releases",
            "--old-release",
            LABTRUST,
            "--new-release",
            COMPUTATION,
        ],
        cwd=REPO_ROOT,
        env=pcs_cli_env(repo_root=REPO_ROOT),
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    payload = json.loads(result.stdout)
    changed = payload.get("changed_computation") or {}
    assert changed.get("dataset_changes") or changed.get("witness_status_changes")
    assert payload.get("changed_workflow_profile")
