import json
import shutil
import tempfile
from pathlib import Path

from sm_pipeline.pcs_import.science_claim_bundle_importer import import_signed_bundle
from sm_pipeline.pcs_import.verification_result_importer import merge_verification_result
from sm_pipeline.pcs_validate.validator import collect_import_warnings

FIXTURES = Path(__file__).resolve().parent / "fixtures"
REPO_ROOT = Path(__file__).resolve().parents[2]


def test_missing_verification_result_warning() -> None:
    bundle = json.loads(
        (FIXTURES / "missing_verification_result.json").read_text(encoding="utf-8")
    )
    warnings = collect_import_warnings(bundle)
    assert any("VerificationResult is absent" in w for w in warnings)

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _copy_schemas(root)
        result = import_signed_bundle(
            FIXTURES / "missing_verification_result.json",
            repo_root=root,
            write=True,
        )
        assert any("VerificationResult is absent" in w for w in result.warnings)
        read_model = json.loads(
            (root / "corpus" / "pcs" / "claims" / result.claim_id / "read_model.json").read_text(
                encoding="utf-8"
            )
        )
        assert read_model.get("verification_result") is None


def test_merge_verification_result_preserves_checks() -> None:
    bundle = json.loads(
        (FIXTURES / "missing_verification_result.json").read_text(encoding="utf-8")
    )
    vr = {
        "schema_version": "VerificationResult.v0",
        "created_at": "2026-05-01T12:00:00Z",
        "producer": "provability-fabric",
        "producer_version": "0.1.0",
        "source_repo": "https://github.com/SentinelOps-CI/provability-fabric",
        "source_commit": "abc",
        "status": "ProofChecked",
        "signature_or_digest": "sha256:vr",
        "checks": [{"id": "c1", "name": "test", "outcome": "pass"}],
    }
    merged = merge_verification_result(bundle, vr)
    assert merged["verification_result"]["checks"][0]["id"] == "c1"


def _copy_schemas(root: Path) -> None:
    dest = root / "schemas" / "pcs"
    dest.mkdir(parents=True)
    for f in (REPO_ROOT / "schemas" / "pcs").glob("*.json"):
        shutil.copy(f, dest / f.name)
