"""Persist Phase 2 release artifacts on claim import."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from sm_pipeline.pcs_import.claim_lineage import build_lineage, write_lineage
from sm_pipeline.pcs_import.release_context import (
    enrich_import_report_with_release_chain,
    enrich_read_model_with_release,
)
from sm_pipeline.pcs_validate.release_chain_validation import require_release_chain_validation
from sm_pipeline.pcs_import.release_manifest_build import RELEASE_MANIFEST_FILENAME

from sm_pipeline.pcs_import.import_report_paths import portable_repo_path
from sm_pipeline.pcs_validate.canonical_hash import canonical_hash


def _load_json(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    return data if isinstance(data, dict) else None


def finalize_release_mode_claim(
    claim_dir: Path,
    bundle_path: Path,
    *,
    repo_root: Path,
    release_validation: dict[str, Any],
    import_report_path: Path,
) -> None:
    release_dir = bundle_path.resolve().parent
    manifest_path = release_dir / RELEASE_MANIFEST_FILENAME
    manifest = _load_json(manifest_path)
    if manifest is None:
        return

    (claim_dir / "release_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (claim_dir / "release_chain_validation.json").write_text(
        json.dumps(release_validation, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    bundle = json.loads(bundle_path.read_text(encoding="utf-8-sig"))
    claim_id = _claim_id_from_read_model(claim_dir) or claim_dir.name
    write_lineage(
        claim_dir,
        build_lineage(
            claim_id=claim_id,
            bundle=bundle,
            signed_bundle_path=bundle_path,
            release_manifest=manifest,
        ),
    )

    if import_report_path.is_file():
        report = _load_json(import_report_path)
        if report is not None:
            report["release_id"] = manifest.get("release_id")
            report["release_candidate"] = manifest.get("release_candidate")
            report["release_manifest_path"] = portable_repo_path(manifest_path, repo_root)
            report["release_manifest_hash"] = canonical_hash(manifest)
            report["validation_profile"] = manifest.get("validation_profile")
            enrich_import_report_with_release_chain(report, release_validation)
            import_report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    read_model_path = claim_dir / "read_model.json"
    read_model = _load_json(read_model_path)
    if read_model is not None:
        enriched = enrich_read_model_with_release(
            read_model,
            manifest=manifest,
            validation=release_validation,
            manifest_path=manifest_path,
            bundle_path=bundle_path,
        )
        read_model_path.write_text(
            json.dumps(enriched, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )


def _claim_id_from_read_model(claim_dir: Path) -> str:
    read_model = _load_json(claim_dir / "read_model.json")
    if read_model is not None:
        return str(read_model.get("claim_id") or "")
    return ""


def load_sibling_release_validation(bundle_path: Path, *, repo_root: Path) -> dict[str, Any]:
    return require_release_chain_validation(
        bundle_path.resolve().parent,
        repo_root=repo_root,
    )
