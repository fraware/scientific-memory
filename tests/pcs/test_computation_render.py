"""Portal read-model sections for scientific computation releases."""

from __future__ import annotations

import json
import shutil
import tempfile
from pathlib import Path

from sm_pipeline.pcs_import.computation_protocol import COMPUTATION_LIMITATION_NOTICE
from sm_pipeline.pcs_import.release_manifest_importer import import_release_manifest

from schema_fixtures import REPO_ROOT, copy_pcs_schemas

FIXTURE = REPO_ROOT / "tests" / "pcs" / "fixtures" / "computation-release"
CLAIM_ID = "claim-computation-release-v0.1"


def _import_computation_read_model() -> dict:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        copy_pcs_schemas(root)
        release_dir = root / "computation-release"
        shutil.copytree(FIXTURE, release_dir)
        import_release_manifest(
            release_dir / "release_manifest.v0.json",
            repo_root=root,
            write=True,
            render=False,
        )
        path = root / "corpus" / "pcs" / "claims" / CLAIM_ID / "read_model.json"
        return json.loads(path.read_text(encoding="utf-8"))


def test_render_computation_receipt_sections() -> None:
    model = _import_computation_read_model()
    assert model.get("domain") == "scientific_computation"
    assert model.get("dataset_receipt", {}).get("id") == "dataset-demo-measurements-v0.1"
    assert model.get("environment_receipt", {}).get("id") == "env-linux-py312-uv"
    assert model.get("computation_run_receipt", {}).get("payload", {}).get("command")
    assert model.get("result_artifact", {}).get("payload", {}).get("sha256", "").startswith("sha256:")
    assert model.get("computation_witness", {}).get("payload", {}).get("status")


def test_render_computation_limitation_notice() -> None:
    model = _import_computation_read_model()
    assert model.get("limitation_notice") == COMPUTATION_LIMITATION_NOTICE
    assert COMPUTATION_LIMITATION_NOTICE in (model.get("limitations") or [])


def test_render_computation_lineage_index_fields() -> None:
    model = _import_computation_read_model()
    computation = (model.get("lineage") or {}).get("computation") or {}
    assert computation.get("dataset_id") == "dataset-demo-measurements-v0.1"
    assert computation.get("environment_id") == "env-linux-py312-uv"
    assert computation.get("code_commit")
    assert computation.get("result_hash", "").startswith("sha256:")
