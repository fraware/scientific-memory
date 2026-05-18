"""Complete scientific_memory_import_report from protocol artifacts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from sm_pipeline.pcs_import.artifact_registry_source import DERIVED_REGISTRY_VERSION
from sm_pipeline.pcs_import.claim_lineage import (
    build_lineage,
    certificate_id_from_bundle,
    trace_hash_from_bundle,
)
from sm_pipeline.pcs_import.import_report_paths import portable_repo_path
from sm_pipeline.pcs_import.release_context import enrich_import_report_with_release_chain
from sm_pipeline.pcs_validate.canonical_hash import canonical_hash, file_sha256_digest


def enrich_import_report_from_protocol(
    report: dict[str, Any],
    *,
    manifest: dict[str, Any],
    validation: dict[str, Any],
    manifest_path: Path,
    bundle_path: Path,
    repo_root: Path,
    artifact_registry_version: str = DERIVED_REGISTRY_VERSION,
) -> None:
    """Populate import report fields from release manifest, chain validation, and bundle."""
    bundle = json.loads(bundle_path.read_text(encoding="utf-8-sig"))
    report["release_id"] = manifest.get("release_id")
    report["release_candidate"] = manifest.get("release_candidate")
    report["release_manifest_path"] = portable_repo_path(manifest_path, repo_root)
    report["release_manifest_hash"] = canonical_hash(manifest)
    report["validation_profile"] = manifest.get("validation_profile")
    report["signed_bundle_hash"] = file_sha256_digest(bundle_path)
    report["certificate_id"] = certificate_id_from_bundle(bundle)
    report["trace_hash"] = trace_hash_from_bundle(bundle)
    report["artifact_registry_version"] = artifact_registry_version
    enrich_import_report_with_release_chain(report, validation)

    lineage = build_lineage(
        claim_id=str(report.get("claim_id") or ""),
        bundle=bundle,
        signed_bundle_path=bundle_path,
        release_manifest=manifest,
    )
    if lineage.get("bundle_id"):
        report["bundle_id"] = lineage["bundle_id"]
