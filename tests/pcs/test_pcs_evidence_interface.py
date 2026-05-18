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
    pcs_cli_env,
    pcs_subprocess_python,
)


def _copy_release(tmp: Path) -> Path:
    import shutil

    dest = tmp / "labtrust-release"
    shutil.copytree(LABTRUST_RELEASE_DIR, dest)
    return dest


def _cli_env(root: Path | None = None) -> dict[str, str]:
    return pcs_cli_env(repo_root=root or REPO_ROOT)


def test_pcs_import_release_command() -> None:
    manifest = (
        LABTRUST_RELEASE_DIR / "ReleaseManifest.v0.json"
    ).relative_to(REPO_ROOT).as_posix()
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
        env=_cli_env(),
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    claim_dir = REPO_ROOT / "corpus" / "pcs" / "claims" / EXPECTED_LABTRUST_CLAIM_ID
    for name in (
        "signed_bundle.json",
        "read_model.json",
        "import_manifest.json",
        "scientific_memory_import_report.json",
        "lineage.json",
        "release_manifest.json",
        "release_chain_validation.json",
        "artifact_registry.json",
        "handoff_manifests.json",
    ):
        assert (claim_dir / name).is_file(), f"missing {name}"
    assert (REPO_ROOT / "portal" / ".generated" / "pcs-export.json").is_file()


def test_pcs_import_release_module_entrypoint() -> None:
    manifest = LABTRUST_RELEASE_DIR / "ReleaseManifest.v0.json"
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        copy_pcs_schemas(root)
        release_dir = _copy_release(root)
        manifest_path = release_dir / "ReleaseManifest.v0.json"
        result = subprocess.run(
            [
                pcs_subprocess_python(),
                "-m",
                "sm_pipeline.pcs_import.release_manifest_importer",
                "--manifest",
                str(manifest_path),
                "--repo-root",
                str(root),
                "--release-mode",
                "--render",
            ],
            cwd=root,
            env=_cli_env(root),
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0, result.stdout + result.stderr
        claim_dir = root / "corpus" / "pcs" / "claims" / EXPECTED_LABTRUST_CLAIM_ID
        for name in (
            "read_model.json",
            "import_manifest.json",
            "lineage.json",
            "scientific_memory_import_report.json",
        ):
            assert (claim_dir / name).is_file(), f"missing {name}"


def test_pcs_list_claims() -> None:
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
        result = subprocess.run(
            [sys.executable, "-m", "sm_pipeline.cli", "pcs-list-claims"],
            cwd=root,
            env=_cli_env(root),
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0
        assert EXPECTED_LABTRUST_CLAIM_ID in result.stdout


def test_pcs_show_claim() -> None:
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
        result = subprocess.run(
            [
                pcs_subprocess_python(),
                "-m",
                "sm_pipeline.cli",
                "pcs-show-claim",
                "--claim-id",
                EXPECTED_LABTRUST_CLAIM_ID,
            ],
            cwd=root,
            env=_cli_env(root),
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0
        payload = json.loads(result.stdout)
        assert payload["claim_id"] == EXPECTED_LABTRUST_CLAIM_ID
        assert isinstance(payload.get("read_model"), dict)
        assert payload["read_model"].get("release_manifest")


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


def test_release_import_does_not_use_fixture_overlay() -> None:
    test_release_manifest_import_does_not_overlay_fixture_report()


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
        bundle_path.write_bytes(bundle_path.read_bytes() + b"\n")

        result = subprocess.run(
            [
                pcs_subprocess_python(),
                "-m",
                "sm_pipeline.cli",
                "pcs-check-stale",
                "--claim-id",
                EXPECTED_LABTRUST_CLAIM_ID,
            ],
            cwd=root,
            env=_cli_env(root),
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0
        payload = json.loads(result.stdout)
        assert payload["claim_id"] == EXPECTED_LABTRUST_CLAIM_ID
        assert payload["stale"] is True
        assert payload.get("claim_state") == "stale"
        assert any("signed_bundle_hash" in reason for reason in payload["stale_reasons"])
        assert "Re-import the current release manifest" in payload["repair_hint"]


def test_pcs_list_claims_by_workflow() -> None:
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
        result = subprocess.run(
            [
                pcs_subprocess_python(),
                "-m",
                "sm_pipeline.cli",
                "pcs-list-claims-by-workflow",
                "--workflow-id",
                "labtrust.qc_release_v0.1",
            ],
            cwd=root,
            env=_cli_env(root),
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0
        assert EXPECTED_LABTRUST_CLAIM_ID in result.stdout


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
        result = subprocess.run(
            [
                pcs_subprocess_python(),
                "-m",
                "sm_pipeline.cli",
                "pcs-list-claims-by-certificate",
                "--certificate-id",
                CANONICAL_RC_CERTIFICATE_ID,
            ],
            cwd=root,
            env=_cli_env(root),
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
