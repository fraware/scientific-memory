"""Claim lineage and stale-dependency tracking for PCS imports."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from sm_pipeline.pcs_import.bundle_utils import bundle_for_validation
from sm_pipeline.pcs_validate.canonical_hash import canonical_hash, file_sha256_digest


def _artifact_id_from_bundle(bundle: dict[str, Any]) -> str:
    scb = bundle.get("science_claim_bundle") or {}
    claim = scb.get("claim_artifact") or scb.get("claim") or {}
    return str(claim.get("id") or claim.get("artifact_id") or "")


def certificate_id_from_bundle(bundle: dict[str, Any]) -> str:
    return _certificate_id(bundle)


def trace_hash_from_bundle(bundle: dict[str, Any]) -> str:
    return _trace_hash(bundle)


def _certificate_id(bundle: dict[str, Any]) -> str:
    scb = bundle.get("science_claim_bundle") or {}
    cert = scb.get("trace_certificate")
    if isinstance(cert, dict):
        return str(cert.get("certificate_id") or cert.get("id") or "")
    certs = scb.get("certificates")
    if isinstance(certs, list) and certs and isinstance(certs[0], dict):
        return str(certs[0].get("certificate_id") or certs[0].get("id") or "")
    return ""


def _trace_hash(bundle: dict[str, Any]) -> str:
    scb = bundle.get("science_claim_bundle") or {}
    receipt = scb.get("runtime_receipt")
    if isinstance(receipt, dict):
        return str(receipt.get("trace_hash") or "")
    receipts = scb.get("runtime_receipts")
    if isinstance(receipts, list) and receipts and isinstance(receipts[0], dict):
        return str(receipts[0].get("trace_hash") or "")
    return ""


def _bundle_id(bundle: dict[str, Any]) -> str:
    scb = bundle.get("science_claim_bundle") or {}
    return str(scb.get("bundle_id") or scb.get("id") or "")


def build_lineage(
    *,
    claim_id: str,
    bundle: dict[str, Any],
    signed_bundle_path: Path,
    release_manifest: dict[str, Any] | None = None,
    workflow_profile_id: str | None = None,
) -> dict[str, Any]:
    scb = bundle_for_validation(bundle)
    producer_repos = {}
    if isinstance(release_manifest, dict):
        producer_repos = release_manifest.get("producer_repos") or {}

    source_commits: dict[str, str] = {}
    if isinstance(producer_repos, dict):
        for key, pin in producer_repos.items():
            if isinstance(pin, dict) and isinstance(pin.get("commit"), str):
                source_commits[key] = pin["commit"]

    schema_versions = {
        "signed_bundle": str(bundle.get("schema_version") or "v0"),
        "science_claim_bundle": str(scb.get("schema_version") or "v0"),
    }

    lineage: dict[str, Any] = {
        "claim_id": claim_id,
        "bundle_id": _bundle_id(bundle),
        "certificate_id": _certificate_id(bundle),
        "trace_hash": _trace_hash(bundle),
        "source_commits": source_commits,
        "schema_versions": schema_versions,
        "signed_bundle_hash": file_sha256_digest(signed_bundle_path),
        "stale": False,
        "stale_reasons": [],
    }
    if workflow_profile_id:
        lineage["workflow_profile_id"] = workflow_profile_id
    if release_manifest is not None:
        lineage["release_id"] = release_manifest.get("release_id")
        lineage["release_manifest_hash"] = canonical_hash(release_manifest)
        artifacts = release_manifest.get("artifacts")
        if isinstance(artifacts, dict):
            lineage["artifact_hashes"] = {
                name: str((entry or {}).get("sha256") or "")
                for name, entry in artifacts.items()
                if isinstance(entry, dict)
            }
    return lineage


def write_lineage(claim_dir: Path, lineage: dict[str, Any]) -> Path:
    path = claim_dir / "lineage.json"
    path.write_text(json.dumps(lineage, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def load_lineage(claim_dir: Path) -> dict[str, Any] | None:
    path = claim_dir / "lineage.json"
    if not path.is_file():
        return None
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    return data if isinstance(data, dict) else None


def check_stale(
    lineage: dict[str, Any],
    *,
    current_bundle_hash: str | None = None,
    current_certificate_id: str | None = None,
    current_trace_hash: str | None = None,
    current_release_manifest_hash: str | None = None,
    current_source_commits: dict[str, str] | None = None,
    current_schema_versions: dict[str, str] | None = None,
    validation_status: str | None = None,
) -> tuple[bool, list[str]]:
    reasons: list[str] = []
    if current_bundle_hash and lineage.get("signed_bundle_hash") != current_bundle_hash:
        reasons.append("signed_bundle_hash changed")
    if current_certificate_id and lineage.get("certificate_id") != current_certificate_id:
        reasons.append("certificate_id changed")
    if current_trace_hash and lineage.get("trace_hash") != current_trace_hash:
        reasons.append("trace_hash changed")
    if (
        current_release_manifest_hash
        and lineage.get("release_manifest_hash")
        and lineage.get("release_manifest_hash") != current_release_manifest_hash
    ):
        reasons.append("release_manifest_hash changed")

    if current_source_commits:
        recorded = lineage.get("source_commits")
        if isinstance(recorded, dict):
            for key, commit in current_source_commits.items():
                if recorded.get(key) != commit:
                    reasons.append(f"source_commit changed ({key})")
                    break

    if current_schema_versions:
        recorded = lineage.get("schema_versions")
        if isinstance(recorded, dict):
            for key, version in current_schema_versions.items():
                if recorded.get(key) != version:
                    reasons.append(f"schema_version changed ({key})")
                    break

    if validation_status and validation_status != "ProofChecked":
        reasons.append("failed revalidation")

    return bool(reasons), reasons


def update_lineage_stale_flags(claim_dir: Path, *, bundle_path: Path | None = None) -> dict[str, Any]:
    lineage = load_lineage(claim_dir)
    if lineage is None:
        raise FileNotFoundError(f"lineage.json not found in {claim_dir}")

    current_bundle_hash = None
    current_certificate_id = None
    current_trace_hash = None
    current_schema_versions: dict[str, str] | None = None
    if bundle_path is not None and bundle_path.is_file():
        bundle = json.loads(bundle_path.read_text(encoding="utf-8-sig"))
        scb = bundle_for_validation(bundle)
        current_bundle_hash = file_sha256_digest(bundle_path)
        current_certificate_id = _certificate_id(bundle)
        current_trace_hash = _trace_hash(bundle)
        current_schema_versions = {
            "signed_bundle": str(bundle.get("schema_version") or "v0"),
            "science_claim_bundle": str(scb.get("schema_version") or "v0"),
        }

    current_manifest_hash = None
    current_source_commits: dict[str, str] | None = None
    manifest_path = claim_dir / "release_manifest.json"
    if manifest_path.is_file():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
        if isinstance(manifest, dict):
            current_manifest_hash = canonical_hash(manifest)
            producer_repos = manifest.get("producer_repos")
            if isinstance(producer_repos, dict):
                current_source_commits = {
                    key: str((pin or {}).get("commit") or "")
                    for key, pin in producer_repos.items()
                    if isinstance(pin, dict) and pin.get("commit")
                }

    validation_status = None
    validation_path = claim_dir / "release_chain_validation.json"
    if validation_path.is_file():
        validation = json.loads(validation_path.read_text(encoding="utf-8-sig"))
        if isinstance(validation, dict):
            validation_status = str(validation.get("status") or "")

    was_stale = bool(lineage.get("stale"))
    stale, reasons = check_stale(
        lineage,
        current_bundle_hash=current_bundle_hash,
        current_certificate_id=current_certificate_id,
        current_trace_hash=current_trace_hash,
        current_release_manifest_hash=current_manifest_hash,
        current_source_commits=current_source_commits,
        current_schema_versions=current_schema_versions,
        validation_status=validation_status,
    )
    lineage["stale"] = stale
    lineage["stale_reasons"] = reasons
    if was_stale and not stale:
        lineage["revalidated"] = True
    write_lineage(claim_dir, lineage)
    return lineage
