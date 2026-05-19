"""Import PCS releases from ReleaseManifest.v0."""

from __future__ import annotations

from pathlib import Path

from sm_pipeline.pcs_import.portal_export import write_pcs_portal_export
from sm_pipeline.pcs_import.release_mode_finalize import finalize_release_mode_claim
from sm_pipeline.pcs_import.science_claim_bundle_importer import ImportResult, import_signed_bundle
from sm_pipeline.pcs_validate.release_chain_validation import require_release_chain_validation
from sm_pipeline.pcs_validate.release_manifest import (
    signed_bundle_path_for_manifest,
    validate_release_manifest_or_raise,
)
from sm_pipeline.pcs_validate.release_paths import resolve_release_manifest_path

def _repo_root(repo_root: Path | None) -> Path:
    if repo_root is not None:
        return repo_root.resolve()
    return Path(__file__).resolve().parents[4]


def _import_root(repo_root: Path) -> Path:
    return repo_root / "corpus" / "pcs" / "claims"


def _resolve_manifest_input(manifest_path: Path) -> Path:
    resolved = manifest_path.resolve()
    if resolved.is_dir():
        return resolve_release_manifest_path(resolved)
    if resolved.is_file():
        return resolved
    parent = resolved.parent
    if parent.is_dir():
        candidate = resolve_release_manifest_path(parent)
        if candidate.is_file():
            return candidate
    return resolved


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
    manifest_file = _resolve_manifest_input(manifest_path)
    manifest = validate_release_manifest_or_raise(manifest_file, repo_root=root)
    release_dir = manifest_file.parent
    validation = require_release_chain_validation(
        release_dir,
        repo_root=root,
        expected_release_id=str(manifest.get("release_id") or ""),
    )

    workflow_profile_id = str(validation.get("workflow_profile_id") or manifest.get("workflow_profile_id") or "")
    workflow_profile = None
    if workflow_profile_id:
        from sm_pipeline.pcs_import.workflow_profile import load_workflow_profile

        workflow_profile = load_workflow_profile(workflow_profile_id, repo_root=root)

    from sm_pipeline.pcs_validate.formal_trust_validation import require_formal_trust_artifacts

    require_formal_trust_artifacts(
        release_dir,
        manifest,
        repo_root=root,
        workflow_profile=workflow_profile,
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


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--manifest",
        "-m",
        type=Path,
        required=True,
        help="ReleaseManifest.v0 JSON path",
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=None,
        help="Scientific Memory repo root (default: parent of pipeline package)",
    )
    parser.add_argument(
        "--release-mode",
        action="store_true",
        default=True,
        help="Strict release import (always enabled; accepted for CLI compatibility)",
    )
    parser.add_argument(
        "--render",
        dest="render",
        action="store_true",
        default=True,
        help="Write portal PCS export after import",
    )
    parser.add_argument(
        "--no-render",
        dest="render",
        action="store_false",
        help="Skip portal export",
    )
    args = parser.parse_args()
    import_release_manifest(
        args.manifest,
        repo_root=args.repo_root,
        write=True,
        render=args.render,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
