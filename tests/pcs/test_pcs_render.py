"""PCS portal read-model / rendering contract tests (PF canonical fixture)."""

import json
import tempfile
from pathlib import Path

from sm_pipeline.pcs_import.artifact_normalizer import LIMITATION_NOTICE, normalize_signed_bundle
from sm_pipeline.pcs_import.science_claim_bundle_importer import import_signed_bundle

from schema_fixtures import PF_SIGNED_BUNDLE, copy_pcs_schemas

FIXTURES = Path(__file__).resolve().parent / "fixtures"

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


def _pf_read_model() -> dict:
    bundle = json.loads(PF_SIGNED_BUNDLE.read_text(encoding="utf-8"))
    return normalize_signed_bundle(bundle)


def test_render_claim_includes_all_required_sections() -> None:
    read_model = _pf_read_model()
    for key in REQUIRED_READ_MODEL_KEYS:
        assert key in read_model, f"missing read_model.{key}"


def test_render_claim_displays_runtime_receipt() -> None:
    read_model = _pf_read_model()
    receipt = read_model["runtime_receipt"]
    assert receipt["id"] == "receipt-qc-release-run-001"
    assert receipt["signature_or_digest"].startswith("sha256:")
    assert str(receipt.get("trace_hash", "")).startswith("sha256:")


def test_render_claim_displays_trace_certificate() -> None:
    read_model = _pf_read_model()
    cert = read_model["trace_certificate"]
    assert cert["id"] == "cert-trace-qc-release-v0.1"
    assert cert["signature_or_digest"].startswith("sha256:")
    assert cert.get("status") == "CertificateChecked"


def test_render_claim_displays_verification_result() -> None:
    read_model = _pf_read_model()
    vr = read_model["verification_result"]
    assert vr is not None
    assert vr.get("verification_id") == "verify-scb-qc-release-v0.1"
    assert vr.get("verifier") == "provability-fabric"
    checks = vr.get("checks") or []
    assert len(checks) >= 1
    assert all(c.get("outcome") == "pass" for c in checks)


def test_render_claim_displays_artifact_hashes() -> None:
    read_model = _pf_read_model()
    digests = read_model["canonical_digests"]
    for key in (
        "claim_artifact",
        "runtime_receipt",
        "trace_certificate",
        "evidence_bundle",
        "signed_bundle",
    ):
        assert digests[key].startswith("sha256:")
    assert len(read_model["artifact_hashes"]) >= 5


def test_render_claim_displays_source_repo_and_source_commit() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _copy_schemas(root)
        result = import_signed_bundle(PF_SIGNED_BUNDLE, repo_root=root, write=True)
        read_model = json.loads(
            (root / "corpus" / "pcs" / "claims" / result.claim_id / "read_model.json").read_text(
                encoding="utf-8"
            )
        )
        repos = {s["source_repo"] for s in read_model["source_repositories"]}
        assert "https://github.com/fraware/LabTrust-Gym" in repos
        commits = {s["source_commit"] for s in read_model["source_repositories"]}
        assert "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa" in commits


def test_render_claim_displays_limitation_notice() -> None:
    read_model = _pf_read_model()
    assert read_model["limitation_notice"] == LIMITATION_NOTICE
    assert LIMITATION_NOTICE in read_model["limitations"]


def _copy_schemas(root: Path) -> None:
    copy_pcs_schemas(root)
