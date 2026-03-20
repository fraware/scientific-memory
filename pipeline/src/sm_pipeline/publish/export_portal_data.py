"""Export canonical portal data bundle from corpus artifacts."""

from __future__ import annotations

import json
from pathlib import Path

from sm_pipeline.publish.portal_read_model import build_portal_bundle


def export_portal_data(repo_root: Path) -> Path:
    """
    Export a single canonical JSON blob for portal consumption.

    The on-disk shape is defined only by ``build_portal_bundle``; the bundle
    ``version`` field matches ``portal_read_model.PORTAL_BUNDLE_VERSION``.

    Output: portal/.generated/corpus-export.json
    """
    repo_root = repo_root.resolve()
    bundle = build_portal_bundle(repo_root)
    out_path = repo_root / "portal" / ".generated" / "corpus-export.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(bundle, indent=2), encoding="utf-8")
    return out_path
