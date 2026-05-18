"""Enrich import reports and read models with release protocol context."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from sm_pipeline.pcs_import.artifact_registry_source import (
    DERIVED_REGISTRY_VERSION,
    load_pcs_core_artifact_registry,
)
from sm_pipeline.pcs_import.import_report_paths import portable_repo_path
from sm_pipeline.pcs_validate.canonical_hash import canonical_hash, file_sha256_digest


def enrich_import_report_with_release_chain(
    report: dict[str, Any],
    validation: dict[str, Any],
) -> None:
    report["release_chain_validation_id"] = validation.get("validation_id")
    report["release_chain_validation_status"] = validation.get("status")
    report["release_chain_validator"] = validation.get("validator")
    report["release_chain_checked_at"] = validation.get("checked_at")


def build_artifact_registry(
    manifest: dict[str, Any],
    validation: dict[str, Any],
    *,
    repo_root: Path | None = None,
) -> list[dict[str, Any]]:
    """Registry rows from ReleaseManifest.v0 artifacts, chain checks, and pcs-core registry."""
    registry_specs: dict[str, Any] = {}
    if repo_root is not None:
        registry_specs, _ = load_pcs_core_artifact_registry(repo_root.resolve())
    checks_by_artifact: dict[str, list[str]] = {}
    for check in validation.get("checks") or []:
        if not isinstance(check, dict):
            continue
        check_id = str(check.get("check_id") or "")
        description = str(check.get("description") or check_id)
        details = check.get("details")
        if isinstance(details, dict):
            for key in details:
                checks_by_artifact.setdefault(key, []).append(description)
        checks_by_artifact.setdefault(check_id, []).append(description)

    registry: list[dict[str, Any]] = []
    artifacts = manifest.get("artifacts")
    if not isinstance(artifacts, dict):
        return registry

    for name, entry in sorted(artifacts.items()):
        if not isinstance(entry, dict):
            continue
        semantic_checks = list(checks_by_artifact.get(name, []))
        if "manifest_hash_alignment" in checks_by_artifact:
            semantic_checks.append("manifest hash alignment")
        artifact_type = str(entry.get("artifact_type") or "")
        spec = registry_specs.get(artifact_type, {})
        if not isinstance(spec, dict):
            spec = {}
        required_fields = spec.get("required_release_fields") or []
        present = [field for field in required_fields if entry.get(field)]
        missing = [field for field in required_fields if field not in present]
        registry.append(
            {
                "name": name,
                "artifact_type": artifact_type,
                "producer": entry.get("producer", ""),
                "schema": entry.get("schema", ""),
                "allowed_statuses": spec.get("allowed_statuses", []),
                "status": manifest.get("release_status", "Validated"),
                "actual_status": entry.get("status") or manifest.get("release_status", "Validated"),
                "source_repo": entry.get("source_repo", ""),
                "source_commit": entry.get("source_commit", ""),
                "hash": entry.get("sha256", ""),
                "semantic_checks_performed": semantic_checks,
                "semantic_checks": spec.get("semantic_checks", []),
                "required_release_fields_present": present,
                "required_release_fields_missing": missing,
                "consumer_repos": spec.get("consumer_repos", []),
                "canonical_hash_required": spec.get("canonical_hash_required", False),
                "release_mode_required": spec.get("release_mode_required", False),
                "registry_admission_result": "admitted" if not missing else "incomplete",
            },
        )
    return registry


def build_artifact_dependency_graph(manifest: dict[str, Any]) -> list[dict[str, str]]:
    """Linear release-chain edges derived from manifest artifact ordering."""
    artifacts = manifest.get("artifacts")
    if not isinstance(artifacts, dict):
        return []
    names = list(artifacts.keys())
    edges: list[dict[str, str]] = []
    for index in range(1, len(names)):
        edges.append({"from": names[index - 1], "to": names[index], "kind": "release_chain"})
    return edges


def build_release_manifest_view(
    manifest: dict[str, Any],
    manifest_path: Path | None,
    *,
    repo_root: Path | None = None,
) -> dict[str, Any]:
    path_value = ""
    if manifest_path is not None:
        path_value = (
            portable_repo_path(manifest_path, repo_root)
            if repo_root is not None
            else manifest_path.as_posix()
        )
    return {
        "release_id": manifest.get("release_id"),
        "release_candidate": manifest.get("release_candidate"),
        "generated_at": manifest.get("generated_at"),
        "validation_profile": manifest.get("validation_profile"),
        "release_status": manifest.get("release_status"),
        "signature_or_digest": manifest.get("signature_or_digest"),
        "manifest_hash": canonical_hash(manifest),
        "manifest_path": path_value,
        "producer_repos": manifest.get("producer_repos", {}),
    }


def build_release_chain_validation_view(validation: dict[str, Any]) -> dict[str, Any]:
    checks_out: list[dict[str, Any]] = []
    for check in validation.get("checks") or []:
        if not isinstance(check, dict):
            continue
        checks_out.append(
            {
                "check_id": check.get("check_id"),
                "description": check.get("description"),
                "status": check.get("status"),
                "details": check.get("details", {}),
            },
        )
    return {
        "validation_id": validation.get("validation_id"),
        "release_id": validation.get("release_id"),
        "release_candidate": validation.get("release_candidate"),
        "validator": validation.get("validator"),
        "validator_version": validation.get("validator_version"),
        "checked_at": validation.get("checked_at"),
        "status": validation.get("status"),
        "artifacts_checked": validation.get("artifacts_checked"),
        "checks": checks_out,
        "failure_codes": validation.get("failure_codes", []),
        "signature_or_digest": validation.get("signature_or_digest"),
    }


def enrich_read_model_with_release(
    read_model: dict[str, Any],
    *,
    manifest: dict[str, Any],
    validation: dict[str, Any],
    manifest_path: Path | None = None,
    bundle_path: Path | None = None,
    repo_root: Path | None = None,
    lineage: dict[str, Any] | None = None,
) -> dict[str, Any]:
    out = dict(read_model)
    out["release_manifest"] = build_release_manifest_view(
        manifest,
        manifest_path,
        repo_root=repo_root,
    )
    out["release_chain_validation"] = build_release_chain_validation_view(validation)
    registry_version = DERIVED_REGISTRY_VERSION
    if repo_root is not None:
        _, registry_version = load_pcs_core_artifact_registry(repo_root.resolve())

    out["artifact_registry"] = build_artifact_registry(
        manifest,
        validation,
        repo_root=repo_root,
    )
    out["artifact_registry_version"] = registry_version
    out["artifact_dependency_graph"] = build_artifact_dependency_graph(manifest)
    if bundle_path is not None and bundle_path.is_file():
        out["signed_bundle_hash"] = file_sha256_digest(bundle_path)
    out["release_manifest_hash"] = canonical_hash(manifest)
    if lineage is not None:
        out["lineage"] = lineage
        out["staleness"] = {
            "stale": bool(lineage.get("stale")),
            "stale_reasons": list(lineage.get("stale_reasons") or []),
        }
    return out
