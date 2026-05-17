"""Enrich import reports and read models with release protocol context."""

from __future__ import annotations

from pathlib import Path
from typing import Any

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


def build_artifact_registry(manifest: dict[str, Any], validation: dict[str, Any]) -> list[dict[str, Any]]:
    """Registry rows from ReleaseManifest.v0 artifacts + chain validation checks."""
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
        registry.append(
            {
                "name": name,
                "artifact_type": entry.get("artifact_type", ""),
                "producer": entry.get("producer", ""),
                "schema": entry.get("schema", ""),
                "status": manifest.get("release_status", "Validated"),
                "source_repo": entry.get("source_repo", ""),
                "source_commit": entry.get("source_commit", ""),
                "hash": entry.get("sha256", ""),
                "semantic_checks_performed": semantic_checks,
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
) -> dict[str, Any]:
    out = dict(read_model)
    out["release_manifest"] = build_release_manifest_view(
        manifest,
        manifest_path,
        repo_root=repo_root,
    )
    out["release_chain_validation"] = build_release_chain_validation_view(validation)
    out["artifact_registry"] = build_artifact_registry(manifest, validation)
    out["artifact_dependency_graph"] = build_artifact_dependency_graph(manifest)
    if bundle_path is not None and bundle_path.is_file():
        out["signed_bundle_hash"] = file_sha256_digest(bundle_path)
    out["release_manifest_hash"] = canonical_hash(manifest)
    return out
