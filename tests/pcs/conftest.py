"""PCS tests: pipeline on PYTHONPATH; unit tests use mirrors unless PCS_INTEGRATION=1."""

import os
import subprocess
import sys
from pathlib import Path

import pytest

_PIPELINE_SRC = Path(__file__).resolve().parents[2] / "pipeline" / "src"
if str(_PIPELINE_SRC) not in sys.path:
    sys.path.insert(0, str(_PIPELINE_SRC))
_PCS_TESTS = Path(__file__).resolve().parent
if str(_PCS_TESTS) not in sys.path:
    sys.path.insert(0, str(_PCS_TESTS))


@pytest.fixture(scope="session", autouse=True)
def _ensure_labtrust_phase2_fixtures() -> None:
    """Keep Phase 2 fixtures aligned (promote_release_run can overwrite import report)."""
    if os.environ.get("PCS_INTEGRATION") == "1":
        return
    repo = Path(__file__).resolve().parents[2]
    script = repo / "scripts" / "ensure_labtrust_phase2_fixtures.py"
    fixture_dir = repo / "tests" / "pcs" / "fixtures" / "labtrust-release"
    if script.is_file() and (fixture_dir / "RELEASE_FIXTURE_MANIFEST.json").is_file():
        subprocess.run(
            [sys.executable, str(script)],
            cwd=repo,
            check=True,
            capture_output=True,
        )
    release_run = repo / "release-run"
    if script.is_file() and (release_run / "RELEASE_FIXTURE_MANIFEST.json").is_file():
        subprocess.run(
            [sys.executable, str(script), "--release-dir", str(release_run)],
            cwd=repo,
            check=True,
            capture_output=True,
        )


@pytest.fixture(scope="session", autouse=True)
def _ensure_tool_use_phase2_fixtures() -> None:
    if os.environ.get("PCS_INTEGRATION") == "1":
        return
    repo = Path(__file__).resolve().parents[2]
    script = repo / "scripts" / "ensure_tool_use_phase2_fixtures.py"
    fixture_dir = repo / "tests" / "pcs" / "fixtures" / "tool-use-release"
    manifest = fixture_dir / "release_manifest.v0.json"
    if script.is_file() and manifest.is_file():
        subprocess.run(
            [sys.executable, str(script)],
            cwd=repo,
            check=True,
            capture_output=True,
        )


@pytest.fixture(autouse=True)
def _unit_tests_use_schema_mirrors(monkeypatch: pytest.MonkeyPatch) -> None:
    """Contract tests use vendored mirrors; set PCS_INTEGRATION=1 for live pcs-core."""
    if os.environ.get("PCS_INTEGRATION") == "1":
        return
    monkeypatch.setattr(
        "sm_pipeline.pcs_validate.validator.validate_with_pcs_core",
        lambda _bundle: [],
    )
