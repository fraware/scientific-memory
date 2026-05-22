#!/usr/bin/env python3
"""Import all PCS release fixtures into corpus/pcs and refresh portal export."""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
RELEASE_MANIFESTS = (
    "tests/pcs/fixtures/labtrust-release/ReleaseManifest.v0.json",
    "tests/pcs/fixtures/tool-use-release/release_manifest.v0.json",
    "tests/pcs/fixtures/computation-release/release_manifest.v0.json",
    "tests/pcs/fixtures/computation-rejected-release/release_manifest.v0.json",
)


def main() -> int:
    sys.path.insert(0, str(REPO_ROOT / "pipeline" / "src"))
    from sm_pipeline.pcs_import.portal_export import write_pcs_portal_export
    from sm_pipeline.pcs_import.release_manifest_importer import import_release_manifest

    for rel in RELEASE_MANIFESTS:
        manifest = REPO_ROOT / rel
        if not manifest.is_file():
            print(f"error: missing {manifest}", file=sys.stderr)
            return 1
        result = import_release_manifest(manifest, repo_root=REPO_ROOT, write=True, render=False)
        print(f"imported {result.claim_id} <- {rel}")

    export_path = write_pcs_portal_export(REPO_ROOT)
    print(f"portal export -> {export_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
