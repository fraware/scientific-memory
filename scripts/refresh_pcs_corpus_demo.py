#!/usr/bin/env python3
"""Re-import PCS demo claims into corpus/pcs/claims/ (canonical + legacy)."""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURES = REPO_ROOT / "tests" / "pcs" / "fixtures"


def main() -> int:
    sys.path.insert(0, str(REPO_ROOT / "pipeline" / "src"))
    from sm_pipeline.pcs_import.portal_export import write_pcs_portal_export
    from sm_pipeline.pcs_import.science_claim_bundle_importer import import_signed_bundle

    canonical = FIXTURES / "signed_science_claim_bundle.valid.json"
    legacy = FIXTURES / "valid_signed_science_claim_bundle.json"
    if not canonical.is_file():
        raise SystemExit(f"Missing canonical fixture: {canonical}")

    legacy_result = import_signed_bundle(
        legacy,
        repo_root=REPO_ROOT,
        strict=True,
        allow_legacy=True,
        write=True,
    )
    print(f"legacy -> {legacy_result.claim_id}")

    core_result = import_signed_bundle(
        canonical,
        repo_root=REPO_ROOT,
        strict=True,
        allow_legacy=False,
        write=True,
    )
    print(f"pcs_core -> {core_result.claim_id}")

    out = write_pcs_portal_export(REPO_ROOT)
    print(f"portal export -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
