import json
import shutil
import tempfile
from pathlib import Path

from sm_pipeline.pcs_import.science_claim_bundle_importer import import_signed_bundle

FIXTURES = Path(__file__).resolve().parent / "fixtures"
REPO_ROOT = Path(__file__).resolve().parents[2]


def test_valid_bundle_imports() -> None:
    bundle_path = FIXTURES / "valid_signed_science_claim_bundle.json"
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _copy_schemas(root)
        result = import_signed_bundle(
            bundle_path,
            repo_root=root,
            write=True,
        )
        assert result.claim_id == "labtrust-qc-release-claim-001"
        read_model_path = (
            root / "corpus" / "pcs" / "claims" / result.claim_id / "read_model.json"
        )
        assert read_model_path.is_file()
        read_model = json.loads(read_model_path.read_text(encoding="utf-8"))
        assert read_model["claim"]["text"]
        assert read_model["source_repositories"]
        assert any(
            s["source_repo"] == "https://github.com/fraware/LabTrust-Gym"
            for s in read_model["source_repositories"]
        )


def test_import_preserves_source_repo_and_commit() -> None:
    bundle_path = FIXTURES / "valid_signed_science_claim_bundle.json"
    raw = json.loads(bundle_path.read_text(encoding="utf-8"))
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _copy_schemas(root)
        import_signed_bundle(bundle_path, repo_root=root, write=True)
        stored = json.loads(
            (root / "corpus" / "pcs" / "claims" / "labtrust-qc-release-claim-001" / "signed_bundle.json").read_text(
                encoding="utf-8"
            )
        )
        scb = stored["science_claim_bundle"]
        assert scb["claim"]["source_repo"] == raw["science_claim_bundle"]["claim"]["source_repo"]
        assert scb["claim"]["source_commit"] == raw["science_claim_bundle"]["claim"]["source_commit"]
        assert scb["claim"]["signature_or_digest"] == raw["science_claim_bundle"]["claim"]["signature_or_digest"]


def _copy_schemas(root: Path) -> None:
    dest = root / "schemas" / "pcs"
    dest.mkdir(parents=True)
    for f in (REPO_ROOT / "schemas" / "pcs").glob("*.json"):
        shutil.copy(f, dest / f.name)
