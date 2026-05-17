"""Copy PCS schema mirrors into a temp repo root for isolated tests."""

from __future__ import annotations

import shutil
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURES = Path(__file__).resolve().parent / "fixtures"

# PF release bundle: provability-fabric/tests/pcs/fixtures/labtrust-release/ (pf sign).
LABTRUST_RELEASE_BUNDLE = FIXTURES / "labtrust-release" / "signed_science_claim_bundle.json"
LABTRUST_RELEASE_MANIFEST = FIXTURES / "labtrust-release" / "RELEASE_FIXTURE_MANIFEST.json"
SM_FIXTURE_MANIFEST = FIXTURES / "labtrust-release" / "FIXTURE_MANIFEST.json"
EXPECTED_LABTRUST_CLAIM_ID = "claim-pcs-qc-release-v0.1"
# Canonical import/render tests use the LabTrust v0.1 release fixture.
PF_SIGNED_BUNDLE = LABTRUST_RELEASE_BUNDLE
LEGACY_SIGNED_BUNDLE = FIXTURES / "valid_signed_science_claim_bundle.json"

IMPORT_REPORT_REQUIRED_KEYS = frozenset(
    {
        "claim_id",
        "verification_status",
        "warnings",
        "stale_artifacts",
        "render_path",
    }
)


def copy_pcs_schemas(root: Path) -> None:
    dest = root / "schemas" / "pcs"
    dest.mkdir(parents=True, exist_ok=True)
    src = REPO_ROOT / "schemas" / "pcs"
    for f in src.glob("*.json"):
        shutil.copy(f, dest / f.name)
    legacy_dest = dest / "legacy"
    legacy_dest.mkdir(exist_ok=True)
    for f in src.glob("legacy/*.json"):
        shutil.copy(f, legacy_dest / f.name)
