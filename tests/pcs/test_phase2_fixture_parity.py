"""Phase 2 fixture alignment with pcs-core examples when available."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from schema_fixtures import (
    LABTRUST_RELEASE_CHAIN_VALIDATION,
    LABTRUST_RELEASE_MANIFEST_V0,
    resolve_pcs_core_root,
)

pytestmark = pytest.mark.skipif(
    not resolve_pcs_core_root().is_dir(),
    reason="pcs-core not available",
)

PCS_EXAMPLES = resolve_pcs_core_root() / "examples"


def test_release_manifest_validates_against_pcs_core_example() -> None:
    from sm_pipeline.pcs_validate.release_manifest import validate_release_manifest

    sm = json.loads(LABTRUST_RELEASE_MANIFEST_V0.read_text(encoding="utf-8-sig"))
    pcs_example = PCS_EXAMPLES / "release_manifest.valid.json"
    if pcs_example.is_file():
        pcs = json.loads(pcs_example.read_text(encoding="utf-8-sig"))
        assert sm["release_id"] == pcs["release_id"]
        assert sm["artifacts"]["signed_science_claim_bundle.json"]["sha256"] == (
            pcs["artifacts"]["signed_science_claim_bundle.json"]["sha256"]
        )
    errors = validate_release_manifest(LABTRUST_RELEASE_MANIFEST_V0)
    assert errors == [], errors


def test_release_chain_validation_matches_pcs_core_release_id() -> None:
    from sm_pipeline.pcs_validate.release_chain_validation import (
        validate_release_chain_validation,
    )

    sm = json.loads(LABTRUST_RELEASE_CHAIN_VALIDATION.read_text(encoding="utf-8-sig"))
    manifest = json.loads(LABTRUST_RELEASE_MANIFEST_V0.read_text(encoding="utf-8-sig"))
    errors = validate_release_chain_validation(
        LABTRUST_RELEASE_CHAIN_VALIDATION,
        expected_release_id=manifest["release_id"],
    )
    assert errors == [], errors
    assert sm["status"] == "ProofChecked"
    pcs_example = PCS_EXAMPLES / "release_chain_validation_result.valid.json"
    if pcs_example.is_file():
        pcs = json.loads(pcs_example.read_text(encoding="utf-8-sig"))
        assert sm["validation_id"] == pcs["validation_id"]
        assert sm["release_id"] == pcs["release_id"]
