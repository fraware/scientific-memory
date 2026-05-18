"""PCS release evidence interface (import command, report, render, stale queries)."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

from sm_pipeline.pcs_import.release_manifest_importer import import_release_manifest
from sm_pipeline.pcs_import.science_claim_bundle_importer import import_signed_bundle
from schema_fixtures import (
    CANONICAL_RC_CERTIFICATE_ID,
    EXPECTED_LABTRUST_CLAIM_ID,
    LABTRUST_RELEASE_BUNDLE,
    LABTRUST_RELEASE_DIR,
    REPO_ROOT,
    copy_pcs_schemas,
)


def _copy_release(tmp: Path) -> Path:
    import shutil

    dest = tmp / "labtrust-release"
    shutil.copytree(LABTRUST_RELEASE_DIR, dest)
    return dest


def test_pcs_import_release_command() -> None:
    manifest = (
        LABTRUST_RELEASE_DIR / "ReleaseManifest.v0.json"
    ).relative_to(REPO_ROOT).as_posix()
    env = os.environ.copy()
    env["PYTHONPATH"] = str(REPO_ROOT / "pipeline" / "src")
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "sm_pipeline.cli",
            "pcs-import-release",
            "--release-manifest",
            manifest,
        ],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    report_path = (
        REPO_ROOT
        / "corpus"
        / "pcs"
        / "claims"
        / EXPECTED_LABTRUST_CLAIM_ID
        / "scientific_memory_import_report.json"
    )
    assert report_path.is_file()


def test_import_report_contains_release_chain_validation_id() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        copy_pcs_schemas(root)
        release_dir = _copy_release(root)
        import_release_manifest(
            release_dir / "ReleaseManifest.v0.json",
            repo_root=root,
            write=True,
            render=False,
        )
        report = json.loads(
            (
                root / "corpus" / "pcs" / "claims" / EXPECTED_LABTRUST_CLAIM_ID
                / "scientific_memory_import_report.json"
            ).read_text(encoding="utf-8"),
        )
        assert report.get("release_chain_validation_id")
        assert report.get("release_chain_validation_status") == "ProofChecked"


def test_import_report_contains_signed_bundle_hash() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        copy_pcs_schemas(root)
        release_dir = _copy_release(root)
        import_release_manifest(
            release_dir / "ReleaseManifest.v0.json",
            repo_root=root,
            write=True,
            render=False,
        )
        report = json.loads(
            (
                root / "corpus" / "pcs" / "claims" / EXPECTED_LABTRUST_CLAIM_ID
                / "scientific_memory_import_report.json"
            ).read_text(encoding="utf-8"),
        )
        assert str(report.get("signed_bundle_hash", "")).startswith("sha256:")
        assert str(report.get("certificate_id", "")).startswith("cert-")
        assert str(report.get("trace_hash", "")).startswith("sha256:")
        assert report.get("artifact_registry_version")


def test_render_lineage_section() -> None:
    from test_release_render import _import_release_read_model

    model = _import_release_read_model()
    lineage = model.get("lineage")
    assert isinstance(lineage, dict)
    assert lineage.get("certificate_id") == CANONICAL_RC_CERTIFICATE_ID
    assert str(lineage.get("signed_bundle_hash", "")).startswith("sha256:")


def test_render_artifact_registry_section() -> None:
    from test_release_render import _import_release_read_model

    model = _import_release_read_model()
    registry = model.get("artifact_registry")
    assert isinstance(registry, list) and registry
    row = next(r for r in registry if r["name"] == "signed_science_claim_bundle.json")
    assert row.get("registry_admission_result") in ("admitted", "incomplete")


def test_release_manifest_import_does_not_overlay_fixture_report() -> None:
    from sm_pipeline.pcs_import.release_manifest_build import write_release_manifest

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        copy_pcs_schemas(root)
        release_dir = _copy_release(root)
        report_path = release_dir / "scientific_memory_import_report.json"
        fixture_report = json.loads(report_path.read_text(encoding="utf-8"))
        fixture_report["release_id"] = "release-BOGUS-OVERLAY"
        report_path.write_text(json.dumps(fixture_report, indent=2) + "\n", encoding="utf-8")
        write_release_manifest(release_dir)
        import_release_manifest(
            release_dir / "ReleaseManifest.v0.json",
            repo_root=root,
            write=True,
            render=False,
        )
        report = json.loads(
            (
                root / "corpus" / "pcs" / "claims" / EXPECTED_LABTRUST_CLAIM_ID
                / "scientific_memory_import_report.json"
            ).read_text(encoding="utf-8"),
        )
        assert report.get("release_id") == "release-pcs-v0.1-labtrust-qc"


def test_pcs_check_stale_detects_signed_bundle_hash_change() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        copy_pcs_schemas(root)
        release_dir = _copy_release(root)
        import_release_manifest(
            release_dir / "ReleaseManifest.v0.json",
            repo_root=root,
            write=True,
            render=False,
        )
        claim_dir = root / "corpus" / "pcs" / "claims" / EXPECTED_LABTRUST_CLAIM_ID
        bundle_path = claim_dir / "signed_bundle.json"
        bundle = json.loads(bundle_path.read_text(encoding="utf-8-sig"))
        bundle["signature_or_digest"] = "sha256:" + "a" * 64
        bundle_path.write_text(json.dumps(bundle, indent=2) + "\n", encoding="utf-8")

        env = os.environ.copy()
        env["PYTHONPATH"] = str(REPO_ROOT / "pipeline" / "src")
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "sm_pipeline.cli",
                "pcs-check-stale",
                "--claim-id",
                EXPECTED_LABTRUST_CLAIM_ID,
            ],
            cwd=root,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0
        assert "Stale" in result.stdout


def test_pcs_list_claims_by_certificate() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        copy_pcs_schemas(root)
        release_dir = _copy_release(root)
        import_release_manifest(
            release_dir / "ReleaseManifest.v0.json",
            repo_root=root,
            write=True,
            render=False,
        )
        env = os.environ.copy()
        env["PYTHONPATH"] = str(REPO_ROOT / "pipeline" / "src")
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "sm_pipeline.cli",
                "pcs-list-claims-by-certificate",
                "--certificate-id",
                CANONICAL_RC_CERTIFICATE_ID,
            ],
            cwd=root,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0
        assert EXPECTED_LABTRUST_CLAIM_ID in result.stdout


def test_bundle_overlay_skipped_outside_pytest_subprocess() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        copy_pcs_schemas(root)
        release_dir = _copy_release(root)
        bundle = release_dir / "signed_science_claim_bundle.json"
        report = release_dir / "scientific_memory_import_report.json"
        report.write_text(
            json.dumps({"release_id": "release-from-fixture-only"}, indent=2) + "\n",
            encoding="utf-8",
        )
        env = os.environ.copy()
        env["PYTHONPATH"] = str(REPO_ROOT / "pipeline" / "src")
        snippet = f"""
import json, warnings
from pathlib import Path
from sm_pipeline.pcs_import.science_claim_bundle_importer import import_signed_bundle
root = Path({str(root)!r})
bundle = root / "labtrust-release" / "signed_science_claim_bundle.json"
with warnings.catch_warnings(record=True) as caught:
    warnings.simplefilter("always")
    import_signed_bundle(bundle, repo_root=root, strict=True, release_mode=True, write=True, pin_fixture_report=True)
msgs = [str(w.message) for w in caught]
assert any("Skipping fixture import-report overlay" in m for m in msgs), msgs
report = json.loads((root / "corpus" / "pcs" / "claims" / "{EXPECTED_LABTRUST_CLAIM_ID}" / "scientific_memory_import_report.json").read_text())
assert report.get("release_id") != "release-from-fixture-only"
"""
        result = subprocess.run(
            [sys.executable, "-c", snippet],
            cwd=root,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0, result.stdout + result.stderr
