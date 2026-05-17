#!/usr/bin/env python3
"""Re-import canonical labtrust release into corpus via ReleaseManifest.v0."""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
MANIFEST = REPO_ROOT / "tests" / "pcs" / "fixtures" / "labtrust-release" / "ReleaseManifest.v0.json"


def main() -> int:
    sys.path.insert(0, str(REPO_ROOT / "pipeline" / "src"))
    from sm_pipeline.pcs_import.portal_export import write_pcs_portal_export
    from sm_pipeline.pcs_import.release_manifest_importer import import_release_manifest

    if not MANIFEST.is_file():
        print(f"error: missing {MANIFEST}", file=sys.stderr)
        return 1

    result = import_release_manifest(MANIFEST, repo_root=REPO_ROOT, write=True, render=True)
    out = write_pcs_portal_export(REPO_ROOT)
    print(f"imported {result.claim_id} -> {result.import_dir}")
    print(f"portal export -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
