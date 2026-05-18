"""CLI: pcs-compare-releases."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

from sm_pipeline.pcs_import.release_compare import compare_releases

from schema_fixtures import copy_pcs_schemas, pcs_cli_env, pcs_subprocess_python


def _write_index(root: Path, entries: list[dict]) -> None:
    pcs = root / "corpus" / "pcs"
    pcs.mkdir(parents=True, exist_ok=True)
    (pcs / "claims_index.json").write_text(
        json.dumps(
            {"schema_version": "PcsClaimsIndex.v0", "claim_count": len(entries), "claims": entries},
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def test_pcs_compare_releases_cli_json() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        copy_pcs_schemas(root)
        for claim_id, release_id, imported_at, bundle_hash in (
            ("claim-a", "release-a", "2026-01-01T00:00:00Z", "sha256:" + "1" * 64),
            ("claim-b", "release-b", "2026-02-01T00:00:00Z", "sha256:" + "2" * 64),
        ):
            claim_dir = root / "corpus" / "pcs" / "claims" / claim_id
            claim_dir.mkdir(parents=True)
            (claim_dir / "lineage.json").write_text(
                json.dumps(
                    {
                        "claim_id": claim_id,
                        "release_id": release_id,
                        "signed_bundle_hash": bundle_hash,
                        "artifact_hashes": {"signed_science_claim_bundle.json": bundle_hash},
                        "stale": False,
                        "stale_reasons": [],
                    },
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
        _write_index(
            root,
            [
                {"claim_id": "claim-a", "claim_dir": "claim-a", "release_id": "release-a", "imported_at": "2026-01-01T00:00:00Z"},
                {"claim_id": "claim-b", "claim_dir": "claim-b", "release_id": "release-b", "imported_at": "2026-02-01T00:00:00Z"},
            ],
        )
        expected = compare_releases(root, old_release_id="release-a", new_release_id="release-b")
        env = pcs_cli_env(repo_root=root)
        result = subprocess.run(
            [
                pcs_subprocess_python(),
                "-m",
                "sm_pipeline.cli",
                "pcs-compare-releases",
                "--old-release",
                "release-a",
                "--new-release",
                "release-b",
            ],
            cwd=root,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0, result.stderr
        payload = json.loads(result.stdout)
        assert payload["old_release_id"] == expected["old_release_id"]
        assert payload["changed_artifacts"] == expected["changed_artifacts"]
