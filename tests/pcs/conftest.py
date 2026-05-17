"""PCS tests: pipeline on PYTHONPATH; unit tests use mirrors unless PCS_INTEGRATION=1."""

import os
import shutil
import sys
from pathlib import Path

import pytest

_PIPELINE_SRC = Path(__file__).resolve().parents[2] / "pipeline" / "src"
if str(_PIPELINE_SRC) not in sys.path:
    sys.path.insert(0, str(_PIPELINE_SRC))
_PCS_TESTS = Path(__file__).resolve().parent
if str(_PCS_TESTS) not in sys.path:
    sys.path.insert(0, str(_PCS_TESTS))


def copy_pcs_schemas(root: Path) -> None:
    dest = root / "schemas" / "pcs"
    dest.mkdir(parents=True, exist_ok=True)
    src = REPO_ROOT / "schemas" / "pcs"
    for f in src.glob("*.json"):
        shutil.copy(f, dest / f.name)
    legacy_dest = dest / "legacy"
    legacy_dest.mkdir(exist_ok=True)
    for f in src.glob("legacy/*.json"):
        shutil.copy(f, legacy_dest / f.name)


@pytest.fixture(autouse=True)
def _unit_tests_use_schema_mirrors(monkeypatch: pytest.MonkeyPatch) -> None:
    """Contract tests use vendored mirrors; set PCS_INTEGRATION=1 for live pcs-core."""
    if os.environ.get("PCS_INTEGRATION") == "1":
        return
    monkeypatch.setattr(
        "sm_pipeline.pcs_validate.validator.validate_with_pcs_core",
        lambda _bundle: [],
    )
