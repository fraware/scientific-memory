"""Copy PCS schema mirrors into a temp repo root for isolated tests."""

from __future__ import annotations

import shutil
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURES = Path(__file__).resolve().parent / "fixtures"

# Canonical PF / PCS Core signed bundle (replace via `pf sign` + `just refresh-pcs-fixtures`).
PF_SIGNED_BUNDLE = FIXTURES / "signed_science_claim_bundle.valid.json"
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
