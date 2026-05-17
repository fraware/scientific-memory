"""Integrity and golden-path tests for PF labtrust-release fixtures."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

from sm_pipeline.pcs_import.artifact_normalizer import LIMITATION_NOTICE, normalize_signed_bundle
from sm_pipeline.pcs_import.science_claim_bundle_importer import import_signed_bundle

from schema_fixtures import (
    EXPECTED_LABTRUST_CLAIM_ID,
    LABTRUST_RELEASE_BUNDLE,
    LABTRUST_RELEASE_MANIFEST,
    copy_pcs_schemas,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
VERIFY_SCRIPT = REPO_ROOT / "scripts" / "verify_labtrust_release_fixture.py"
FIXTURES = Path(__file__).resolve().parent / "fixtures"
CANONICAL_READ_MODEL = FIXTURES / "canonical_pcs_read_model.json"


def test_labtrust_release_fixture_manifest_is_current() -> None:
    assert VERIFY_SCRIPT.is_file()
    result = subprocess.run(
        [sys.executable, str(VERIFY_SCRIPT)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_labtrust_release_signed_bundle_claim_id() -> None:
    manifest = json.loads(LABTRUST_RELEASE_MANIFEST.read_text(encoding="utf-8"))
    bundle = json.loads(LABTRUST_RELEASE_BUNDLE.read_text(encoding="utf-8"))
    claim_id = bundle["science_claim_bundle"]["claim_artifact"]["artifact_id"]
    assert claim_id == manifest["expected_claim_id"]
    assert claim_id == EXPECTED_LABTRUST_CLAIM_ID


def test_import_read_model_matches_canonical_golden_fixture() -> None:
    """Import PF signed bundle; read_model must match committed canonical_pcs_read_model.json."""
    assert CANONICAL_READ_MODEL.is_file()
    golden = json.loads(CANONICAL_READ_MODEL.read_text(encoding="utf-8"))
    normalized = normalize_signed_bundle(
        json.loads(LABTRUST_RELEASE_BUNDLE.read_text(encoding="utf-8"))
    )
    assert normalized == golden
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        copy_pcs_schemas(root)
        result = import_signed_bundle(LABTRUST_RELEASE_BUNDLE, repo_root=root, write=True)
        assert result.claim_id == EXPECTED_LABTRUST_CLAIM_ID
        imported = json.loads(
            (root / "corpus" / "pcs" / "claims" / result.claim_id / "read_model.json").read_text(
                encoding="utf-8"
            )
        )
        assert imported == golden
        assert imported["limitation_notice"] == LIMITATION_NOTICE


def test_pcs_corpus_claim_passes_validate_all_gate() -> None:
    from sm_pipeline.validate.pcs_corpus import validate_pcs_corpus

    validate_pcs_corpus(REPO_ROOT)
