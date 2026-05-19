"""PCS portal UI contract (static hooks + read model + node zod script)."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from sm_pipeline.pcs_import.artifact_normalizer import LIMITATION_NOTICE

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURES = Path(__file__).resolve().parent / "fixtures"
PCS_COMPONENTS = REPO_ROOT / "portal" / "components" / "pcs"

PCS_UI_SECTION_TESTIDS = (
    "pcs-section-claim",
    "pcs-section-workflow-profile",
    "pcs-section-assumptions",
    "pcs-section-runtime-evidence",
    "pcs-section-dataset-receipt",
    "pcs-section-environment-receipt",
    "pcs-section-computation-run-receipt",
    "pcs-section-result-artifact",
    "pcs-section-computation-witness",
    "pcs-computation-witness-failures",
    "pcs-section-tool-use-trace",
    "pcs-section-tool-use-certificate",
    "pcs-section-temporal-certificate",
    "pcs-section-verification-result",
    "pcs-section-release-manifest",
    "pcs-section-release-chain-validation",
    "pcs-section-artifact-registry",
    "pcs-section-handoff-manifests",
    "pcs-section-artifact-dependency-graph",
    "pcs-section-lineage",
    "pcs-section-staleness",
    "pcs-section-artifact-hashes",
    "pcs-section-source-repos",
    "pcs-section-reproduce-verify",
    "pcs-limitation-notice",
)


def test_pcs_portal_components_define_section_testids() -> None:
    sources = "\n".join(
        p.read_text(encoding="utf-8") for p in PCS_COMPONENTS.glob("*.tsx")
    )
    for testid in PCS_UI_SECTION_TESTIDS:
        present = f'data-testid="{testid}"' in sources or f'testId="{testid}"' in sources
        assert present, f"missing portal hook {testid}"


def test_canonical_read_model_matches_portal_contract() -> None:
    read_model = json.loads(
        (FIXTURES / "canonical_pcs_read_model.json").read_text(encoding="utf-8")
    )
    assert read_model["limitation_notice"] == LIMITATION_NOTICE
    assert read_model["verification_result"] is not None
    assert len(read_model["artifact_hashes"]) >= 5
    assert read_model["canonical_digests"]["signed_bundle"].startswith("sha256:")


def test_computation_phase2_read_model_fixture_passes_portal_contract() -> None:
    script = REPO_ROOT / "portal" / "scripts" / "verify-pcs-phase2-read-model.mjs"
    read_model = (
        REPO_ROOT / "tests" / "pcs" / "fixtures" / "computation-release" / ".phase2-read-model.json"
    )
    if not read_model.is_file():
        pytest.skip("computation .phase2-read-model.json missing; run: just bootstrap-computation-release")

    result = subprocess.run(
        ["node", str(script), str(read_model)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_computation_rejected_phase2_read_model_fixture_passes_portal_contract() -> None:
    script = REPO_ROOT / "portal" / "scripts" / "verify-pcs-phase2-read-model.mjs"
    read_model = (
        REPO_ROOT
        / "tests"
        / "pcs"
        / "fixtures"
        / "computation-rejected-release"
        / ".phase2-read-model.json"
    )
    if not read_model.is_file():
        pytest.skip(
            "computation-rejected .phase2-read-model.json missing; run: just bootstrap-computation-release",
        )

    result = subprocess.run(
        ["node", str(script), str(read_model)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_tool_use_phase2_read_model_fixture_passes_portal_contract() -> None:
    script = REPO_ROOT / "portal" / "scripts" / "verify-pcs-phase2-read-model.mjs"
    read_model = REPO_ROOT / "tests" / "pcs" / "fixtures" / "tool-use-release" / ".phase2-read-model.json"
    if not read_model.is_file():
        pytest.skip("tool-use .phase2-read-model.json missing; run: just sync-tool-use-release")

    result = subprocess.run(
        ["node", str(script), str(read_model)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_pcs_portal_phase2_read_model_script_passes() -> None:
    script = REPO_ROOT / "portal" / "scripts" / "verify-pcs-phase2-read-model.mjs"
    read_model = (
        REPO_ROOT / "corpus" / "pcs" / "claims" / "claim-pcs-qc-release-v0.1" / "read_model.json"
    )
    if not read_model.is_file():
        pytest.skip("corpus PCS claim not imported; run: just pcs-import-release")

    result = subprocess.run(
        ["node", str(script), str(read_model)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_pcs_portal_read_model_script_passes() -> None:
    script = REPO_ROOT / "portal" / "scripts" / "verify-pcs-read-model.mjs"
    result = subprocess.run(
        ["node", str(script)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr


