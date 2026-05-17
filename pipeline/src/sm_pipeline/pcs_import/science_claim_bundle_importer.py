"""Import signed LabTrust ScienceClaimBundle artifacts."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sm_pipeline.pcs_import.artifact_normalizer import normalize_signed_bundle
from sm_pipeline.pcs_import.bundle_utils import bundle_for_validation
from sm_pipeline.pcs_import.provenance import git_head_commit
from sm_pipeline.pcs_validate.bundle_detection import detect_bundle_shape
from sm_pipeline.pcs_validate.stale_checker import find_stale_artifacts
from sm_pipeline.pcs_validate.validator import (
    BundleValidationError,
    validate_signed_bundle,
    verification_status_label,
)


@dataclass
class ImportResult:
    claim_id: str
    import_dir: Path
    warnings: list[str] = field(default_factory=list)
    stale_artifacts: list[str] = field(default_factory=list)
    verification_status: str = "absent"
    render_path: str = ""


def _repo_root(repo_root: Path | None) -> Path:
    if repo_root is not None:
        return repo_root.resolve()
    return Path(__file__).resolve().parents[4]


def _import_root(repo_root: Path) -> Path:
    return repo_root / "corpus" / "pcs" / "claims"


def import_signed_bundle(
    bundle_path: Path,
    *,
    repo_root: Path | None = None,
    strict: bool = True,
    allow_legacy: bool = False,
    write: bool = True,
) -> ImportResult:
    """
    Validate and import a signed science claim bundle.

    Preserves artifact IDs, source_repo, source_commit, signature_or_digest,
    and verification checks. Rejects invalid bundles when strict=True.
    """
    root = _repo_root(repo_root)
    raw = json.loads(bundle_path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise BundleValidationError("Bundle must be a JSON object")

    warnings = validate_signed_bundle(
        bundle_for_validation(raw),
        repo_root=root,
        strict=strict,
        allow_legacy=allow_legacy,
    )
    stale = find_stale_artifacts(raw)
    if stale:
        warnings.extend(f"Stale or deprecated artifact: {p}" for p in stale)

    bundle_shape = detect_bundle_shape(raw)
    read_model = normalize_signed_bundle(raw)
    claim_id = read_model["claim_id"]
    render_path = f"/pcs/claims/{claim_id}"
    verification_status = verification_status_label(raw)

    import_dir = _import_root(root) / claim_id

    if write:
        import_dir.mkdir(parents=True, exist_ok=True)
        (import_dir / "signed_bundle.json").write_text(
            json.dumps(raw, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        (import_dir / "read_model.json").write_text(
            json.dumps(read_model, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        manifest = {
            "claim_id": claim_id,
            "imported_from": str(bundle_path.resolve()),
            "warnings": warnings,
            "stale_artifacts": stale,
        }
        (import_dir / "import_manifest.json").write_text(
            json.dumps(manifest, indent=2) + "\n",
            encoding="utf-8",
        )
        imported_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
        if imported_at.endswith("+00:00"):
            imported_at = imported_at[:-6] + "Z"
        import_report: dict[str, Any] = {
            "claim_id": claim_id,
            "imported_at": imported_at,
            "source_bundle_path": str(bundle_path.resolve()),
            "bundle_shape": bundle_shape,
            "strict": strict,
            "allow_legacy": allow_legacy,
            "verification_status": verification_status,
            "warnings": warnings,
            "stale_artifacts": stale,
            "render_path": render_path,
        }
        sm_commit = git_head_commit(root)
        if sm_commit:
            import_report["scientific_memory_commit"] = sm_commit
        (import_dir / "scientific_memory_import_report.json").write_text(
            json.dumps(import_report, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    return ImportResult(
        claim_id=claim_id,
        import_dir=import_dir,
        warnings=warnings,
        stale_artifacts=stale,
        verification_status=verification_status,
        render_path=render_path,
    )


def load_read_model(repo_root: Path, claim_id: str) -> dict[str, Any] | None:
    path = _import_root(repo_root.resolve()) / claim_id / "read_model.json"
    if not path.is_file():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else None
