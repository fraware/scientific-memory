"""Integration tests with live pcs-core (run: PCS_INTEGRATION=1 pytest tests/pcs/test_pcs_integration.py)."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

pytestmark = pytest.mark.skipif(
    os.environ.get("PCS_INTEGRATION") != "1",
    reason="Set PCS_INTEGRATION=1 to run live pcs-core validation",
)

pcs_core = pytest.importorskip("pcs_core")

from sm_pipeline.pcs_import.science_claim_bundle_importer import import_signed_bundle
from sm_pipeline.pcs_validate.pcs_core_hook import validate_with_pcs_core

from schema_fixtures import copy_pcs_schemas

FIXTURES = Path(__file__).resolve().parent / "fixtures"
REPO_ROOT = Path(__file__).resolve().parents[2]


def test_pcs_core_validates_official_example() -> None:
    bundle = json.loads(
        (FIXTURES / "signed_science_claim_bundle.json").read_text(encoding="utf-8")
    )
    errors = validate_with_pcs_core(bundle)
    assert errors == []


def test_pcs_core_bundle_imports_end_to_end(tmp_path: Path) -> None:
    root = tmp_path
    _copy_schemas(root)
    result = import_signed_bundle(
        FIXTURES / "signed_science_claim_bundle.json",
        repo_root=root,
        write=True,
    )
    report = json.loads(
        (
            root
            / "corpus"
            / "pcs"
            / "claims"
            / result.claim_id
            / "scientific_memory_import_report.json"
        ).read_text(encoding="utf-8")
    )
    assert report["verification_status"] == "passed"


def _copy_schemas(root: Path) -> None:
    copy_pcs_schemas(root)
