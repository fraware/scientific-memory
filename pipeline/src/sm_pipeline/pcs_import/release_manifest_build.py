"""Build ReleaseManifest.v0 from labtrust-release fixture layout (consumer-side)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from sm_pipeline.pcs_validate.canonical_hash import canonical_hash, file_sha256_digest

RELEASE_MANIFEST_FILENAME = "ReleaseManifest.v0.json"
LEGACY_MANIFEST_FILENAME = "RELEASE_FIXTURE_MANIFEST.json"

_ARTIFACT_META: dict[str, tuple[str, str, str, str]] = {
    "trace.json": (
        "LabTrust.Trace.v0",
        "trace.json",
        "LabTrust-Gym",
        "https://github.com/fraware/LabTrust-Gym",
    ),
    "runtime_receipt.json": (
        "RuntimeReceipt.v0",
        "RuntimeReceipt.v0.schema.json",
        "LabTrust-Gym",
        "https://github.com/fraware/LabTrust-Gym",
    ),
    "trace_certificate.json": (
        "TraceCertificate.v0",
        "TraceCertificate.v0.schema.json",
        "CertifyEdge",
        "https://github.com/fraware/CertifyEdge",
    ),
    "science_claim_bundle.pending.json": (
        "ScienceClaimBundle.v0",
        "ScienceClaimBundle.v0.schema.json",
        "LabTrust-Gym",
        "https://github.com/fraware/LabTrust-Gym",
    ),
    "science_claim_bundle.certified.json": (
        "ScienceClaimBundle.v0",
        "ScienceClaimBundle.v0.schema.json",
        "LabTrust-Gym",
        "https://github.com/fraware/LabTrust-Gym",
    ),
    "verification_result.json": (
        "VerificationResult.v0",
        "VerificationResult.v0.schema.json",
        "Provability Fabric",
        "https://github.com/SentinelOps-CI/provability-fabric",
    ),
    "signed_science_claim_bundle.json": (
        "SignedScienceClaimBundle.v0",
        "SignedScienceClaimBundle.v0.schema.json",
        "Provability Fabric",
        "https://github.com/SentinelOps-CI/provability-fabric",
    ),
    "scientific_memory_import_report.json": (
        "ScientificMemory.ImportReport.v0",
        "scientific_memory_import_report.json",
        "Scientific Memory",
        "https://github.com/fraware/scientific-memory",
    ),
}

_COMMIT_KEYS = {
    "pcs_core": "pcs_core_commit",
    "labtrust_gym": "labtrust_gym_commit",
    "certifyedge": "certifyedge_commit",
    "provability_fabric": "provability_fabric_commit",
    "scientific_memory": "scientific_memory_commit",
}


def build_release_manifest_from_release_dir(release_dir: Path) -> dict[str, Any]:
    legacy_path = release_dir / LEGACY_MANIFEST_FILENAME
    if not legacy_path.is_file():
        raise FileNotFoundError(f"missing {legacy_path}")

    legacy = json.loads(legacy_path.read_text(encoding="utf-8-sig"))
    artifacts_legacy = legacy.get("artifacts")
    if not isinstance(artifacts_legacy, dict):
        raise ValueError("RELEASE_FIXTURE_MANIFEST.json artifacts must be an object")

    artifacts: dict[str, Any] = {}
    for name, digest in artifacts_legacy.items():
        meta = _ARTIFACT_META.get(name)
        if meta is None:
            continue
        artifact_type, schema, producer, default_repo = meta
        commit_key = None
        if producer == "LabTrust-Gym":
            commit_key = legacy.get("labtrust_gym_commit")
        elif producer == "CertifyEdge":
            commit_key = legacy.get("certifyedge_commit")
        elif producer == "Provability Fabric":
            commit_key = legacy.get("provability_fabric_commit")
        elif producer == "Scientific Memory":
            commit_key = legacy.get("scientific_memory_commit")
        path = release_dir / name
        sha256 = digest if isinstance(digest, str) else file_sha256_digest(path)
        if path.is_file():
            sha256 = file_sha256_digest(path)
        artifacts[name] = {
            "artifact_type": artifact_type,
            "schema": schema,
            "producer": producer,
            "source_repo": default_repo,
            "source_commit": commit_key or "",
            "sha256": sha256,
        }

    producer_repos = {
        key: {
            "repo": {
                "pcs_core": "https://github.com/SentinelOps-CI/pcs-core",
                "labtrust_gym": "https://github.com/fraware/LabTrust-Gym",
                "certifyedge": "https://github.com/fraware/CertifyEdge",
                "provability_fabric": "https://github.com/SentinelOps-CI/provability-fabric",
                "scientific_memory": "https://github.com/fraware/scientific-memory",
            }[key],
            "commit": legacy[legacy_key],
        }
        for key, legacy_key in _COMMIT_KEYS.items()
        if isinstance(legacy.get(legacy_key), str)
    }

    body: dict[str, Any] = {
        "schema_version": "v0",
        "release_id": "release-pcs-v0.1-labtrust-qc",
        "release_candidate": legacy.get("release_candidate", "pcs-v0.1.0-rc1"),
        "generated_at": legacy.get("generated_at", ""),
        "validation_profile": "labtrust-v0.1-release-chain",
        "producer_repos": producer_repos,
        "artifacts": artifacts,
        "release_status": "Validated",
    }
    body["signature_or_digest"] = canonical_hash(body)
    return body


def write_release_manifest(release_dir: Path) -> Path:
    manifest = build_release_manifest_from_release_dir(release_dir)
    out = release_dir / RELEASE_MANIFEST_FILENAME
    out.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return out
