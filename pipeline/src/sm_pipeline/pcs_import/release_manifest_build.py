"""Build ReleaseManifest.v0 from labtrust-release fixture layout (consumer-side)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from sm_pipeline.pcs_validate.canonical_hash import canonical_hash, file_sha256_digest

RELEASE_MANIFEST_FILENAME = "ReleaseManifest.v0.json"
RELEASE_CHAIN_VALIDATION_FILENAME = "ReleaseChainValidationResult.v0.json"
LEGACY_MANIFEST_FILENAME = "RELEASE_FIXTURE_MANIFEST.json"
CANONICAL_CLAIM_ID = "claim-pcs-qc-release-v0.1"
LABTRUST_WORKFLOW_PROFILE_ID = "labtrust.qc_release_v0.1"
LIMITATIONS_NOTICE = (
    "PCS v0.1 demonstrates a proof-carrying simulated lab workflow; "
    "it does not claim clinical validity or production certification."
)

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
    "proof_obligation.v0.json": (
        "ProofObligation.v0",
        "ProofObligation.v0.schema.json",
        "pcs-core",
        "https://github.com/SentinelOps-CI/pcs-core",
    ),
    "lean_check_result.v0.json": (
        "LeanCheckResult.v0",
        "LeanCheckResult.v0.schema.json",
        "pcs-core",
        "https://github.com/SentinelOps-CI/pcs-core",
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
        elif producer == "pcs-core":
            commit_key = legacy.get("pcs_core_commit")
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

    pcs_commit = legacy.get("pcs_core_commit") or ""
    for name in ("proof_obligation.v0.json", "lean_check_result.v0.json"):
        path = release_dir / name
        if not path.is_file():
            continue
        meta = _ARTIFACT_META.get(name)
        if meta is None:
            continue
        artifact_type, schema, producer, default_repo = meta
        artifacts[name] = {
            "artifact_type": artifact_type,
            "schema": schema,
            "producer": producer,
            "source_repo": default_repo,
            "source_commit": pcs_commit,
            "sha256": file_sha256_digest(path),
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

    certified_hash = str(artifacts_legacy.get("science_claim_bundle.certified.json", ""))
    signed_hash = str(artifacts_legacy.get("signed_science_claim_bundle.json", ""))
    trace_hash = _trace_hash_from_release_dir(release_dir)
    certificate_id = _certificate_id_from_release_dir(release_dir)
    validation_path = release_dir / RELEASE_CHAIN_VALIDATION_FILENAME
    validation_digest = (
        file_sha256_digest(validation_path) if validation_path.is_file() else signed_hash
    )

    body: dict[str, Any] = {
        "schema_version": "v0",
        "release_id": "release-pcs-v0.1-labtrust-qc",
        "release_candidate": legacy.get("release_candidate", "pcs-v0.1.0-rc1"),
        "generated_at": legacy.get("generated_at", ""),
        "validation_profile": "labtrust-v0.1-release-chain",
        "workflow_profile_id": LABTRUST_WORKFLOW_PROFILE_ID,
        "chain_root": {
            "trace_hash": trace_hash,
            "certificate_id": certificate_id,
            "certified_bundle_hash": certified_hash,
            "signed_bundle_hash": signed_hash,
        },
        "release_chain_validation_result": {
            "path": RELEASE_CHAIN_VALIDATION_FILENAME,
            "sha256": validation_digest,
        },
        "canonical_signed_bundle": {
            "path": "signed_science_claim_bundle.json",
            "sha256": signed_hash,
        },
        "canonical_claim_id": CANONICAL_CLAIM_ID,
        "limitations_notice": LIMITATIONS_NOTICE,
        "producer_repos": producer_repos,
        "artifacts": artifacts,
        "release_status": "Validated",
    }
    body["signature_or_digest"] = canonical_hash(body)
    return body


def _trace_hash_from_release_dir(release_dir: Path) -> str:
    trace_path = release_dir / "trace.json"
    if trace_path.is_file():
        trace = json.loads(trace_path.read_text(encoding="utf-8-sig"))
        if isinstance(trace, dict) and isinstance(trace.get("trace_hash"), str):
            return trace["trace_hash"]
    receipt_path = release_dir / "runtime_receipt.json"
    if receipt_path.is_file():
        receipt = json.loads(receipt_path.read_text(encoding="utf-8-sig"))
        if isinstance(receipt, dict) and isinstance(receipt.get("trace_hash"), str):
            return receipt["trace_hash"]
    return ""


def _certificate_id_from_release_dir(release_dir: Path) -> str:
    cert_path = release_dir / "trace_certificate.json"
    if not cert_path.is_file():
        return ""
    cert = json.loads(cert_path.read_text(encoding="utf-8-sig"))
    if isinstance(cert, dict) and isinstance(cert.get("certificate_id"), str):
        return cert["certificate_id"]
    return ""


def write_release_manifest(release_dir: Path) -> Path:
    manifest = build_release_manifest_from_release_dir(release_dir)
    out = release_dir / RELEASE_MANIFEST_FILENAME
    out.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return out
