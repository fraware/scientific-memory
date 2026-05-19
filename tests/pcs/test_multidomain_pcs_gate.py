"""Cross-workflow PCS gate: LabTrust, tool-use, and computation releases import and export together."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from schema_fixtures import REPO_ROOT, pcs_cli_env, pcs_subprocess_python

PORTAL_SCRIPT = REPO_ROOT / "portal" / "scripts" / "verify-pcs-phase2-read-model.mjs"

RELEASES = (
    (
        "labtrust",
        REPO_ROOT / "tests/pcs/fixtures/labtrust-release/ReleaseManifest.v0.json",
        "claim-pcs-qc-release-v0.1",
        "labtrust.qc_release_v0.1",
    ),
    (
        "tool-use",
        REPO_ROOT / "tests/pcs/fixtures/tool-use-release/release_manifest.v0.json",
        "claim-qc-release-v0.1",
        "agent_tool_use.safety_v0",
    ),
    (
        "computation",
        REPO_ROOT / "tests/pcs/fixtures/computation-release/release_manifest.v0.json",
        "claim-computation-release-v0.1",
        "scientific_computation.reproducibility_v0",
    ),
)


def _import_manifest(manifest: Path) -> None:
    result = subprocess.run(
        [
            pcs_subprocess_python(),
            "-m",
            "sm_pipeline.cli",
            "pcs-import-release",
            "--release-manifest",
            str(manifest.relative_to(REPO_ROOT)),
        ],
        cwd=REPO_ROOT,
        env=pcs_cli_env(repo_root=REPO_ROOT),
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.fixture(scope="module", autouse=True)
def _import_all_domains() -> None:
    for _label, manifest, _claim_id, _workflow in RELEASES:
        if not manifest.is_file():
            pytest.skip(f"missing manifest: {manifest}")
        _import_manifest(manifest)


def test_multidomain_corpus_claims_present() -> None:
    index = json.loads((REPO_ROOT / "corpus/pcs/claims_index.json").read_text(encoding="utf-8"))
    indexed_ids = {entry.get("claim_id") for entry in index.get("claims") or []}
    for _label, _manifest, claim_id, _workflow in RELEASES:
        assert claim_id in indexed_ids


def test_multidomain_portal_export_includes_all_workflows() -> None:
    export_path = REPO_ROOT / "portal" / ".generated" / "pcs-export.json"
    result = subprocess.run(
        [
            pcs_subprocess_python(),
            "-m",
            "sm_pipeline.cli",
            "pcs-render-claim",
            "--claim-id",
            "claim-pcs-qc-release-v0.1",
        ],
        cwd=REPO_ROOT,
        env=pcs_cli_env(repo_root=REPO_ROOT),
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert export_path.is_file()

    export = json.loads(export_path.read_text(encoding="utf-8"))
    claims = export.get("claims") or {}
    for _label, _manifest, claim_id, workflow_id in RELEASES:
        model = claims.get(claim_id)
        assert model is not None, f"missing export for {claim_id}"
        assert model.get("workflow_id") == workflow_id


@pytest.mark.parametrize(
    ("label", "phase2_path"),
    [
        ("labtrust", REPO_ROOT / "corpus/pcs/claims/claim-pcs-qc-release-v0.1/read_model.json"),
        (
            "tool-use",
            REPO_ROOT / "tests/pcs/fixtures/tool-use-release/.phase2-read-model.json",
        ),
        (
            "computation",
            REPO_ROOT / "tests/pcs/fixtures/computation-release/.phase2-read-model.json",
        ),
    ],
)
def test_multidomain_phase2_read_models_pass_portal_contract(label: str, phase2_path: Path) -> None:
    if not phase2_path.is_file():
        pytest.skip(f"{label} read model missing at {phase2_path}")
    if not PORTAL_SCRIPT.is_file():
        pytest.skip("portal phase2 script missing")

    result = subprocess.run(
        ["node", str(PORTAL_SCRIPT), str(phase2_path)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, f"{label}: {result.stdout}\n{result.stderr}"


def test_multidomain_compare_labtrust_to_computation() -> None:
    result = subprocess.run(
        [
            pcs_subprocess_python(),
            "-m",
            "sm_pipeline.cli",
            "pcs-compare-releases",
            "--old-release",
            "release-pcs-v0.1-labtrust-qc",
            "--new-release",
            "release-pcs-v0.1-scientific-computation-reproducibility",
        ],
        cwd=REPO_ROOT,
        env=pcs_cli_env(repo_root=REPO_ROOT),
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    assert payload.get("changed_workflow_profile")
    assert payload.get("changed_computation")
