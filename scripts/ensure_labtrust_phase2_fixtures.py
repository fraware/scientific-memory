#!/usr/bin/env python3
"""Ensure Phase 2 protocol fixtures exist beside labtrust-release chain artifacts."""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DIR = REPO_ROOT / "tests" / "pcs" / "fixtures" / "labtrust-release"
PCS_CORE_EXAMPLES = REPO_ROOT.parent / "pcs-core" / "examples"

PHASE2_FILES = (
    "ReleaseManifest.v0.json",
    "ReleaseChainValidationResult.v0.json",
)

IMPORT_REPORT_TEMPLATE = {
    "allow_legacy": False,
    "bundle_shape": "pcs_core",
    "claim_id": "claim-pcs-qc-release-v0.1",
    "imported_at": "2026-05-17T15:39:09Z",
    "render_path": "/pcs/claims/claim-pcs-qc-release-v0.1",
    "scientific_memory_commit": "5b4b81049b430d1b59ff5b51f688eb0feaeef76c",
    "source_bundle_path": "tests/pcs/fixtures/labtrust-release/signed_science_claim_bundle.json",
    "stale_artifacts": [],
    "strict": True,
    "verification_status": "passed",
    "warnings": [],
    "source_repo": "https://github.com/fraware/scientific-memory",
    "source_commit": "5b4b81049b430d1b59ff5b51f688eb0feaeef76c",
    "release_id": "release-pcs-v0.1-labtrust-qc",
    "release_candidate": "pcs-v0.1.0-rc1",
    "release_manifest_path": "tests/pcs/fixtures/labtrust-release/ReleaseManifest.v0.json",
    "validation_profile": "labtrust-v0.1-release-chain",
    "release_chain_validation_id": "validation-pcs-v0.1-labtrust-qc-rc",
    "release_chain_validation_status": "ProofChecked",
    "release_chain_validator": "pcs-core",
    "release_chain_checked_at": "2026-05-17T17:01:22Z",
}


def _sync_legacy_manifest_artifact_hashes(release_dir: Path) -> None:
    import json

    from sm_pipeline.pcs_validate.canonical_hash import file_sha256_digest

    legacy_path = release_dir / "RELEASE_FIXTURE_MANIFEST.json"
    legacy = json.loads(legacy_path.read_text(encoding="utf-8-sig"))
    artifacts = legacy.get("artifacts")
    if isinstance(artifacts, dict):
        for name in list(artifacts):
            path = release_dir / name
            if path.is_file():
                artifacts[name] = file_sha256_digest(path)
    legacy_path.write_text(json.dumps(legacy, indent=2) + "\n", encoding="utf-8")


def _write_canonical_import_report(release_dir: Path) -> None:
    import json

    report_path = release_dir / "scientific_memory_import_report.json"
    # release_manifest_hash is added during live import only (not part of manifest artifact hash).
    report_path.write_text(json.dumps(IMPORT_REPORT_TEMPLATE, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--release-dir", type=Path, default=DEFAULT_DIR)
    args = parser.parse_args()
    release_dir = args.release_dir.resolve()
    if not (release_dir / "RELEASE_FIXTURE_MANIFEST.json").is_file():
        print(f"error: missing legacy manifest in {release_dir}", file=sys.stderr)
        return 1

    sys.path.insert(0, str(REPO_ROOT / "pipeline" / "src"))
    from sm_pipeline.pcs_import.release_manifest_build import write_release_manifest
    from sm_pipeline.pcs_validate.release_chain_validation import validate_release_chain_validation
    from sm_pipeline.pcs_validate.release_manifest import validate_release_manifest

    _write_canonical_import_report(release_dir)

    pcs_labtrust = PCS_CORE_EXAMPLES / "labtrust-release"
    validation_aliases = (
        ("release_chain_validation_result.v0.json", "ReleaseChainValidationResult.v0.json"),
    )
    for pcs_name, dest_name in validation_aliases:
        pcs_src = pcs_labtrust / pcs_name
        dest = release_dir / dest_name
        if pcs_src.is_file():
            shutil.copy2(pcs_src, dest)
            print(f"copied pcs-core example -> {dest}")

    for name in PHASE2_FILES:
        dest = release_dir / name
        if name == "ReleaseManifest.v0.json":
            continue
        pcs_src = PCS_CORE_EXAMPLES / name
        if not pcs_src.is_file():
            pcs_src = pcs_labtrust / name
        if pcs_src.is_file():
            shutil.copy2(pcs_src, dest)
            print(f"copied pcs-core example -> {dest}")

    out = write_release_manifest(release_dir)
    print(f"generated {out}")

    _sync_legacy_manifest_artifact_hashes(release_dir)

    manifest_path = release_dir / "ReleaseManifest.v0.json"
    validation_path = release_dir / "ReleaseChainValidationResult.v0.json"
    if not validation_path.is_file():
        for candidate in (
            PCS_CORE_EXAMPLES / "release_chain_validation_result.valid.json",
            PCS_CORE_EXAMPLES / "ReleaseChainValidationResult.v0.json",
        ):
            if candidate.is_file():
                shutil.copy2(candidate, validation_path)
                print(f"copied pcs-core example -> {validation_path}")
                break
        if not validation_path.is_file():
            print(f"error: missing {validation_path}", file=sys.stderr)
            return 1

    manifest_errors = validate_release_manifest(manifest_path, repo_root=REPO_ROOT)
    if manifest_errors:
        for err in manifest_errors:
            print(f"error: manifest: {err}", file=sys.stderr)
        return 1

    manifest = __import__("json").loads(manifest_path.read_text(encoding="utf-8-sig"))
    validation_errors = validate_release_chain_validation(
        validation_path,
        repo_root=REPO_ROOT,
        expected_release_id=str(manifest.get("release_id") or ""),
    )
    if validation_errors:
        for err in validation_errors:
            print(f"error: validation: {err}", file=sys.stderr)
        return 1

    print(f"OK: Phase 2 fixtures valid in {release_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
