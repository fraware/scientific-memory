"""Corpus-wide PCS claim index and cross-claim lineage queries."""

from __future__ import annotations

import json
import shutil
import tempfile
from pathlib import Path

from sm_pipeline.pcs_import.claim_index import (
    build_claims_index,
    query_claims_index,
    write_claims_index,
)
from sm_pipeline.pcs_import.claim_query import (
    list_claims_by_release_id,
    list_claims_by_trace_hash,
    refresh_all_stale_flags,
)
from sm_pipeline.pcs_import.release_manifest_importer import import_release_manifest

from schema_fixtures import (
    CANONICAL_RC_CERTIFICATE_ID,
    CANONICAL_RC_TRACE_HASH,
    EXPECTED_LABTRUST_CLAIM_ID,
    LABTRUST_RELEASE_DIR,
    copy_pcs_schemas,
)


def _import(root: Path) -> None:
    release_dir = root / "labtrust-release"
    shutil.copytree(LABTRUST_RELEASE_DIR, release_dir)
    import_release_manifest(
        release_dir / "ReleaseManifest.v0.json",
        repo_root=root,
        write=True,
        render=False,
    )


def test_claims_index_written_on_import() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        copy_pcs_schemas(root)
        _import(root)
        index_path = root / "corpus" / "pcs" / "claims_index.json"
        assert index_path.is_file()
        index = json.loads(index_path.read_text(encoding="utf-8"))
        assert index["claim_count"] >= 1
        assert any(c["claim_id"] == EXPECTED_LABTRUST_CLAIM_ID for c in index["claims"])


def test_query_claims_by_release_id() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        copy_pcs_schemas(root)
        _import(root)
        matches = list_claims_by_release_id(root, "release-pcs-v0.1-labtrust-qc")
        assert EXPECTED_LABTRUST_CLAIM_ID in matches


def test_query_claims_by_trace_hash() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        copy_pcs_schemas(root)
        _import(root)
        matches = list_claims_by_trace_hash(root, CANONICAL_RC_TRACE_HASH)
        assert EXPECTED_LABTRUST_CLAIM_ID in matches


def test_query_claims_index_by_certificate() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        copy_pcs_schemas(root)
        _import(root)
        rows = query_claims_index(root, certificate_id=CANONICAL_RC_CERTIFICATE_ID)
        assert any(row["claim_id"] == EXPECTED_LABTRUST_CLAIM_ID for row in rows)


def test_refresh_stale_updates_index() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        copy_pcs_schemas(root)
        _import(root)
        claim_dir = root / "corpus" / "pcs" / "claims" / EXPECTED_LABTRUST_CLAIM_ID
        bundle_path = claim_dir / "signed_bundle.json"
        bundle = json.loads(bundle_path.read_text(encoding="utf-8-sig"))
        bundle["signature_or_digest"] = "sha256:" + "b" * 64
        bundle_path.write_text(json.dumps(bundle, indent=2) + "\n", encoding="utf-8")
        refresh_all_stale_flags(root)
        index = build_claims_index(root)
        entry = next(c for c in index["claims"] if c["claim_id"] == EXPECTED_LABTRUST_CLAIM_ID)
        assert entry["stale"] is True
        write_claims_index(root)
