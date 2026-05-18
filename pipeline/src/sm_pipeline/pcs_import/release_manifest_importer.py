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
    parser.add_argument("--manifest", "-m", type=Path, required=True)
    parser.add_argument("--no-render", action="store_true")
    args = parser.parse_args()
    import_release_manifest(
        args.manifest,
        write=True,
        render=not args.no_render,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
