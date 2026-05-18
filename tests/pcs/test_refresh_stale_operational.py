"""refresh_all_stale_flags writes operational lineage/staleness into read_model."""

from __future__ import annotations

import json
import shutil
import tempfile
from pathlib import Path

from sm_pipeline.pcs_import.claim_query import refresh_all_stale_flags
from sm_pipeline.pcs_import.release_manifest_importer import import_release_manifest

from schema_fixtures import EXPECTED_LABTRUST_CLAIM_ID, LABTRUST_RELEASE_DIR, copy_pcs_schemas


def test_refresh_stale_updates_operational_views_in_read_model() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        copy_pcs_schemas(root)
        release_dir = root / "labtrust-release"
        shutil.copytree(LABTRUST_RELEASE_DIR, release_dir)
        import_release_manifest(
            release_dir / "ReleaseManifest.v0.json",
            repo_root=root,
            write=True,
            render=False,
        )
        claim_dir = root / "corpus" / "pcs" / "claims" / EXPECTED_LABTRUST_CLAIM_ID
        bundle_path = claim_dir / "signed_bundle.json"
        bundle_path.write_bytes(bundle_path.read_bytes() + b"\n")

        refresh_all_stale_flags(root)

        read_model = json.loads((claim_dir / "read_model.json").read_text(encoding="utf-8"))
        staleness = read_model["staleness"]
        assert staleness["stale"] is True
        assert staleness.get("claim_state") == "stale"
        assert staleness.get("repair_hint")
        assert staleness.get("recommended_action")
        lineage = read_model["lineage"]
        assert lineage.get("claim_state") == "stale"
        assert lineage.get("recommended_action")
