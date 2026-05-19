#!/usr/bin/env python3
"""Write portal-contract .phase2-read-model.json beside a PCS release fixture directory."""

from __future__ import annotations

import shutil
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def write_phase2_read_model_fixture(
    release_dir: Path,
    *,
    repo_root: Path | None = None,
) -> Path:
    """Import release in a temp repo and copy read_model.json to .phase2-read-model.json."""
    root = (repo_root or REPO_ROOT).resolve()
    release_dir = release_dir.resolve()
    sys.path.insert(0, str(root / "pipeline" / "src"))
    from sm_pipeline.pcs_import.release_manifest_importer import import_release_manifest
    from sm_pipeline.pcs_validate.release_paths import resolve_release_manifest_path

    schemas_src = root / "schemas"
    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp)
        if schemas_src.is_dir():
            shutil.copytree(schemas_src, work / "schemas")
        dest = work / "release"
        shutil.copytree(release_dir, dest)
        manifest = resolve_release_manifest_path(dest)
        result = import_release_manifest(manifest, repo_root=work, write=True, render=False)
        read_model = work / "corpus" / "pcs" / "claims" / result.claim_id / "read_model.json"
        out = release_dir / ".phase2-read-model.json"
        shutil.copy2(read_model, out)
        return out
