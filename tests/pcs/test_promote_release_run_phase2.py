"""Regression: promote_release_run must not strip Phase 2 import report fields."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
PROMOTE = REPO_ROOT / "scripts" / "promote_release_run.py"
FIXTURES = Path(__file__).resolve().parent / "fixtures" / "labtrust-release"


@pytest.mark.skipif(not PROMOTE.is_file(), reason="promote_release_run.py missing")
def test_promote_then_ensure_preserves_phase2_import_report() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        run_dir = Path(tmp) / "release-run"
        target = Path(tmp) / "fixtures" / "labtrust-release"
        run_dir.mkdir(parents=True)
        for name in (
            "trace.json",
            "runtime_receipt.json",
            "trace_certificate.json",
            "science_claim_bundle.pending.json",
            "science_claim_bundle.certified.json",
            "verification_result.json",
            "signed_science_claim_bundle.json",
            "scientific_memory_import_report.json",
            "RELEASE_FIXTURE_MANIFEST.json",
        ):
            shutil_copy = __import__("shutil").copy2
            shutil_copy(FIXTURES / name, run_dir / name)

        result = subprocess.run(
            [sys.executable, str(PROMOTE), "--run-dir", str(run_dir), "--target", str(target)],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, result.stdout + result.stderr

        report = json.loads(
            (target / "scientific_memory_import_report.json").read_text(encoding="utf-8"),
        )
        assert report.get("release_chain_validation_status") == "ProofChecked"
        assert report.get("release_id") == "release-pcs-v0.1-labtrust-qc"
        assert (target / "ReleaseManifest.v0.json").is_file()
        assert (target / "ReleaseChainValidationResult.v0.json").is_file()
