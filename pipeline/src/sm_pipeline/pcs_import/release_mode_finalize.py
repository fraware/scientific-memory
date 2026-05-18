"""Persist Phase 2 release artifacts on claim import."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from sm_pipeline.pcs_import.artifact_registry_source import load_artifact_registry_v0
from sm_pipeline.pcs_import.handoff_manifest import load_release_handoffs
from sm_pipeline.pcs_import.claim_lineage import build_lineage, update_lineage_stale_flags, write_lineage
from sm_pipeline.pcs_import.import_report_enrichment import enrich_import_report_from_protocol
from sm_pipeline.pcs_import.release_context import enrich_read_model_with_release
from sm_pipeline.pcs_validate.release_chain_validation import require_release_chain_validation
from sm_pipeline.pcs_validate.release_paths import resolve_release_manifest_path

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
    manifest_path = resolve_release_manifest_path(release_dir)
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

    signed_in_claim = claim_dir / "signed_bundle.json"
    lineage_bundle_path = signed_in_claim if signed_in_claim.is_file() else bundle_path
    bundle = json.loads(lineage_bundle_path.read_text(encoding="utf-8-sig"))
    claim_id = _claim_id_from_read_model(claim_dir) or claim_dir.name
    workflow_profile_id = str(release_validation.get("workflow_profile_id") or "")
    lineage = build_lineage(
        claim_id=claim_id,
        bundle=bundle,
        signed_bundle_path=lineage_bundle_path,
        release_manifest=manifest,
        workflow_profile_id=workflow_profile_id or None,
    )
    write_lineage(claim_dir, lineage)
    lineage = update_lineage_stale_flags(claim_dir, bundle_path=lineage_bundle_path)

    if workflow_profile_id:
        from sm_pipeline.pcs_import.workflow_profile import load_workflow_profile

        profile = load_workflow_profile(workflow_profile_id, repo_root=repo_root)
        if profile is not None:
            (claim_dir / "workflow_profile.json").write_text(
                json.dumps(profile, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )

    registry_artifact, registry_version, _ = load_artifact_registry_v0(
        repo_root,
        release_dir=release_dir,
        validate=True,
    )
    if registry_artifact is not None:
        (claim_dir / "artifact_registry.json").write_text(
            json.dumps(registry_artifact, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    handoffs = load_release_handoffs(release_dir, repo_root=repo_root)
    if handoffs:
        (claim_dir / "handoff_manifests.json").write_text(
            json.dumps(handoffs, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    if import_report_path.is_file():
        report = _load_json(import_report_path)
        if report is not None:
            enrich_import_report_from_protocol(
                report,
                manifest=manifest,
                validation=release_validation,
                manifest_path=manifest_path,
                bundle_path=bundle_path,
                repo_root=repo_root,
                artifact_registry_version=registry_version,
            )
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
            repo_root=repo_root,
            lineage=lineage,
        )
        read_model_path.write_text(
            json.dumps(enriched, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    from sm_pipeline.pcs_import.claim_index import write_claims_index

    write_claims_index(repo_root)


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
