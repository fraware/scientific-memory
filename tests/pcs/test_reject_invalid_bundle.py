import shutil
import tempfile
from pathlib import Path

import pytest

from sm_pipeline.pcs_import.science_claim_bundle_importer import import_signed_bundle
from sm_pipeline.pcs_validate.validator import BundleValidationError, validate_signed_bundle

FIXTURES = Path(__file__).resolve().parent / "fixtures"
REPO_ROOT = Path(__file__).resolve().parents[2]


def test_invalid_bundle_rejected() -> None:
    import json

    bundle = json.loads(
        (FIXTURES / "invalid_missing_signature.json").read_text(encoding="utf-8")
    )
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _copy_schemas(root)
        with pytest.raises(BundleValidationError):
            validate_signed_bundle(bundle, repo_root=root, strict=True)


def test_missing_assumption_rejected() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _copy_schemas(root)
        with pytest.raises(BundleValidationError):
            import_signed_bundle(
                FIXTURES / "missing_assumptions.json",
                repo_root=root,
                write=False,
            )


def _copy_schemas(root: Path) -> None:
    dest = root / "schemas" / "pcs"
    dest.mkdir(parents=True)
    for f in (REPO_ROOT / "schemas" / "pcs").glob("*.json"):
        shutil.copy(f, dest / f.name)
