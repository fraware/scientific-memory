import json
import shutil
import tempfile
from pathlib import Path

from sm_pipeline.pcs_import.science_claim_bundle_importer import import_signed_bundle

FIXTURES = Path(__file__).resolve().parent / "fixtures"
REPO_ROOT = Path(__file__).resolve().parents[2]


def test_pcs_core_signed_bundle_imports() -> None:
    bundle_path = FIXTURES / "valid_signed_pcs_core_bundle.json"
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _copy_schemas(root)
        result = import_signed_bundle(bundle_path, repo_root=root, write=True)
        assert result.claim_id == "claim-qc-release-v0.1"
        read_model = json.loads(
            (root / "corpus" / "pcs" / "claims" / result.claim_id / "read_model.json").read_text(
                encoding="utf-8"
            )
        )
        assert read_model["claim"]["text"]
        assert read_model["trace_certificate"]["status"] == "CertificateChecked"
        assert read_model["verification_result"] is not None
        assert read_model["verification_result"]["checks"][0]["outcome"] == "pass"
        assert any(h["name"] == "trace_hash" for h in read_model["artifact_hashes"])


def _copy_schemas(root: Path) -> None:
    dest = root / "schemas" / "pcs"
    dest.mkdir(parents=True)
    for f in (REPO_ROOT / "schemas" / "pcs").glob("*.json"):
        shutil.copy(f, dest / f.name)
