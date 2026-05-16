import json
import shutil
import tempfile
from pathlib import Path

from sm_pipeline.pcs_import.artifact_normalizer import LIMITATION_NOTICE, normalize_signed_bundle
from sm_pipeline.pcs_import.science_claim_bundle_importer import import_signed_bundle

FIXTURES = Path(__file__).resolve().parent / "fixtures"
REPO_ROOT = Path(__file__).resolve().parents[2]

REQUIRED_READ_MODEL_KEYS = (
    "claim",
    "assumption_set",
    "runtime_receipt",
    "trace_certificate",
    "artifact_hashes",
    "source_repositories",
    "reproduce_commands",
    "verify_commands",
    "limitations",
    "limitation_notice",
)


def test_portal_read_model_has_all_required_sections() -> None:
    bundle = json.loads(
        (FIXTURES / "valid_signed_science_claim_bundle.json").read_text(encoding="utf-8")
    )
    read_model = normalize_signed_bundle(bundle)
    for key in REQUIRED_READ_MODEL_KEYS:
        assert key in read_model, f"missing read_model.{key}"


def test_limitations_notice_present() -> None:
    bundle = json.loads(
        (FIXTURES / "valid_signed_science_claim_bundle.json").read_text(encoding="utf-8")
    )
    read_model = normalize_signed_bundle(bundle)
    assert read_model["limitation_notice"] == LIMITATION_NOTICE
    assert LIMITATION_NOTICE in read_model["limitations"]


def test_artifact_hashes_displayed() -> None:
    bundle = json.loads(
        (FIXTURES / "valid_signed_science_claim_bundle.json").read_text(encoding="utf-8")
    )
    read_model = normalize_signed_bundle(bundle)
    assert len(read_model["artifact_hashes"]) >= 1
    assert all("digest" in row and "name" in row for row in read_model["artifact_hashes"])


def test_source_repo_and_commit_displayed() -> None:
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


def test_status_values_preserved() -> None:
    bundle = json.loads(
        (FIXTURES / "valid_signed_science_claim_bundle.json").read_text(encoding="utf-8")
    )
    read_model = normalize_signed_bundle(bundle)
    assert read_model["claim"]["status"] == "RuntimeChecked"
    assert read_model["trace_certificate"]["status"] == "CertificateChecked"
    vr = read_model["verification_result"]
    assert vr is not None
    assert vr["status"] == "ProofChecked"


def _copy_schemas(root: Path) -> None:
    dest = root / "schemas" / "pcs"
    dest.mkdir(parents=True)
    for f in (REPO_ROOT / "schemas" / "pcs").glob("*.json"):
        shutil.copy(f, dest / f.name)
