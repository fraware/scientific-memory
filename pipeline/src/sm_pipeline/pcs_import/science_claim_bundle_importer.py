"""Import signed LabTrust ScienceClaimBundle artifacts."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from sm_pipeline.pcs_import.artifact_normalizer import normalize_signed_bundle
from sm_pipeline.pcs_validate.stale_checker import find_stale_artifacts
from sm_pipeline.pcs_validate.validator import BundleValidationError, validate_signed_bundle


@dataclass
class ImportResult:
    claim_id: str
    import_dir: Path
    warnings: list[str] = field(default_factory=list)
    stale_artifacts: list[str] = field(default_factory=list)


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

    warnings = validate_signed_bundle(raw, repo_root=root, strict=strict)
    stale = find_stale_artifacts(raw)
    if stale:
        warnings.extend(f"Stale or deprecated artifact: {p}" for p in stale)

    read_model = normalize_signed_bundle(raw)
    claim_id = read_model["claim_id"]
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

    return ImportResult(
        claim_id=claim_id,
        import_dir=import_dir,
        warnings=warnings,
        stale_artifacts=stale,
    )


def load_read_model(repo_root: Path, claim_id: str) -> dict[str, Any] | None:
    path = _import_root(repo_root.resolve()) / claim_id / "read_model.json"
    if not path.is_file():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else None
