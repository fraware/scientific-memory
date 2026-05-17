"""Import PCS releases from ReleaseManifest.v0."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from sm_pipeline.pcs_import.import_report_paths import portable_repo_path
from sm_pipeline.pcs_import.portal_export import write_pcs_portal_export
from sm_pipeline.pcs_import.release_mode_finalize import finalize_release_mode_claim
from sm_pipeline.pcs_import.science_claim_bundle_importer import ImportResult, import_signed_bundle
from sm_pipeline.pcs_validate.canonical_hash import canonical_hash
from sm_pipeline.pcs_validate.release_chain_validation import require_release_chain_validation
from sm_pipeline.pcs_validate.release_manifest import (
    signed_bundle_path_for_manifest,
    validate_release_manifest_or_raise,
)

def _repo_root(repo_root: Path | None) -> Path:
    if repo_root is not None:
        return repo_root.resolve()
    return Path(__file__).resolve().parents[4]


def _import_root(repo_root: Path) -> Path:
    return repo_root / "corpus" / "pcs" / "claims"


def import_release_manifest(
    manifest_path: Path,
    *,
    repo_root: Path | None = None,
    write: bool = True,
    render: bool = True,
) -> ImportResult:
    """
    Load ReleaseManifest.v0, validate against pcs-core protocol, import signed bundle.

    Validates manifest digests, locates signed_science_claim_bundle.json, imports in
    strict release mode, writes import report, and optionally renders portal export.
    """
    root = _repo_root(repo_root)
    manifest_file = manifest_path.resolve()
    manifest = validate_release_manifest_or_raise(manifest_file, repo_root=root)
    release_dir = manifest_file.parent
    validation = require_release_chain_validation(
        release_dir,
        repo_root=root,
        expected_release_id=str(manifest.get("release_id") or ""),
    )
    bundle_path = signed_bundle_path_for_manifest(manifest_file)

    result = import_signed_bundle(
        bundle_path,
        repo_root=root,
        strict=True,
        release_mode=True,
        allow_legacy=False,
        write=write,
        pin_fixture_report=False,
    )

    if write:
        claim_dir = _import_root(root) / result.claim_id
        report_path = claim_dir / "scientific_memory_import_report.json"
        if report_path.is_file():
            report = json.loads(report_path.read_text(encoding="utf-8-sig"))
            if isinstance(report, dict):
                _enrich_import_report(
                    report,
                    manifest=manifest,
                    manifest_path=manifest_file,
                    repo_root=root,
                )
                report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        finalize_release_mode_claim(
            claim_dir,
            bundle_path,
            repo_root=root,
            release_validation=validation,
            import_report_path=report_path,
        )

    if render and write:
        write_pcs_portal_export(root, claim_id=result.claim_id)

    return result


def _enrich_import_report(
    report: dict[str, Any],
    *,
    manifest: dict[str, Any],
    manifest_path: Path,
    repo_root: Path,
) -> None:
    report["release_id"] = manifest.get("release_id")
    report["release_candidate"] = manifest.get("release_candidate")
    report["release_manifest_path"] = portable_repo_path(manifest_path, repo_root)
    report["release_manifest_hash"] = canonical_hash(manifest)
    report["validation_profile"] = manifest.get("validation_profile")
