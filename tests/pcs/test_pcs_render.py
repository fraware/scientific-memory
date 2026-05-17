"""PCS portal read-model / rendering contract tests."""

import json
import shutil
import tempfile
from pathlib import Path

from sm_pipeline.pcs_import.artifact_normalizer import LIMITATION_NOTICE, normalize_signed_bundle
from sm_pipeline.pcs_import.science_claim_bundle_importer import import_signed_bundle

from schema_fixtures import copy_pcs_schemas

FIXTURES = Path(__file__).resolve().parent / "fixtures"
REPO_ROOT = Path(__file__).resolve().parents[2]

REQUIRED_READ_MODEL_KEYS = (
    "claim",
    "assumption_set",
    "runtime_receipt",
    "trace_certificate",
    "evidence_bundle",
    "verification_result",
    "artifact_hashes",
    "canonical_digests",
    "source_repositories",
    "reproduce_commands",
    "verify_commands",
    "limitations",
    "limitation_notice",
)

CANONICAL_DIGEST_KEYS = (
    "claim_artifact",
    "runtime_receipt",
    "trace_certificate",
    "evidence_bundle",
    "signed_bundle",
)


def test_render_claim_includes_all_required_sections() -> None:
    bundle = json.loads(
        (FIXTURES / "valid_signed_science_claim_bundle.json").read_text(encoding="utf-8")
    )
    read_model = normalize_signed_bundle(bundle)
    for key in REQUIRED_READ_MODEL_KEYS:
        assert key in read_model, f"missing read_model.{key}"


def test_render_claim_includes_limitation_notice() -> None:
    bundle = json.loads(
        (FIXTURES / "valid_signed_science_claim_bundle.json").read_text(encoding="utf-8")
    )
    read_model = normalize_signed_bundle(bundle)
    assert read_model["limitation_notice"] == LIMITATION_NOTICE
    assert LIMITATION_NOTICE in read_model["limitations"]


def test_render_claim_displays_source_repo_and_source_commit() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _copy_schemas(root)
        result = import_signed_bundle(
            FIXTURES / "valid_signed_science_claim_bundle.json",
            repo_root=root,
            write=True,
        )
        read_model = json.loads(
            (root / "corpus" / "pcs" / "claims" / result.claim_id / "read_model.json").read_text(
                encoding="utf-8"
            )
        )
        repos = {s["source_repo"] for s in read_model["source_repositories"]}
        assert "https://github.com/fraware/LabTrust-Gym" in repos
        commits = {s["source_commit"] for s in read_model["source_repositories"]}
        assert "labtrust-qc-release-demo" in commits


def test_render_claim_displays_artifact_hashes() -> None:
    bundle = json.loads(
        (FIXTURES / "valid_signed_pcs_core_bundle.json").read_text(encoding="utf-8")
    )
    read_model = normalize_signed_bundle(bundle)
    digests = read_model["canonical_digests"]
    for key in CANONICAL_DIGEST_KEYS:
        assert key in digests
    assert digests["claim_artifact"].startswith("sha256:")
    assert digests["runtime_receipt"].startswith("sha256:")
    assert digests["trace_certificate"].startswith("sha256:")
    assert digests["signed_bundle"].startswith("sha256:")
    assert len(read_model["artifact_hashes"]) >= 5


def _copy_schemas(root: Path) -> None:
    copy_pcs_schemas(root)
