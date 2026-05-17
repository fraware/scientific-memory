"""PCS portal UI contract (static hooks + read model; optional vitest when installed)."""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

from sm_pipeline.pcs_import.artifact_normalizer import LIMITATION_NOTICE

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURES = Path(__file__).resolve().parent / "fixtures"
PCS_COMPONENTS = REPO_ROOT / "portal" / "components" / "pcs"

PCS_UI_SECTION_TESTIDS = (
    "pcs-section-claim",
    "pcs-section-assumptions",
    "pcs-section-runtime-evidence",
    "pcs-section-temporal-certificate",
    "pcs-section-verification-result",
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
        assert f'data-testid="{testid}"' in sources, f"missing portal hook {testid}"


def test_canonical_read_model_matches_portal_contract() -> None:
    read_model = json.loads(
        (FIXTURES / "canonical_pcs_read_model.json").read_text(encoding="utf-8")
    )
    assert read_model["limitation_notice"] == LIMITATION_NOTICE
    assert read_model["verification_result"] is not None
    assert len(read_model["artifact_hashes"]) >= 5
    assert read_model["canonical_digests"]["signed_bundle"].startswith("sha256:")


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


@pytest.mark.skipif(
    shutil.which("pnpm") is None
    or not (REPO_ROOT / "portal" / "node_modules" / ".bin" / "vitest").exists(),
    reason="portal vitest not installed (run pnpm install when registry TLS allows)",
)
def test_pcs_portal_vitest_when_available() -> None:
    result = subprocess.run(
        ["pnpm", "--dir", "portal", "test"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
