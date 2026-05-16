"""Normalize PCS nested artifacts into a portal read model."""

from __future__ import annotations

from typing import Any

GUARANTEE_KEYS = (
    "formally_checked",
    "certificate_checked",
    "runtime_observed",
    "empirically_measured",
    "human_reviewed",
    "unchecked_advisory",
)

LIMITATION_NOTICE = (
    "This artifact is a proof-carrying simulation result. It demonstrates "
    "protocol-level and runtime-evidence verification inside LabTrust-Gym. It is "
    "not a clinical validation, production medical certification, or guarantee "
    "about a real hospital laboratory."
)


def _hash_rows(artifact: dict[str, Any] | None) -> list[dict[str, str]]:
    if not isinstance(artifact, dict):
        return []
    rows: list[dict[str, str]] = []
    for field in ("input_hashes", "output_hashes"):
        entries = artifact.get(field)
        if not isinstance(entries, list):
            continue
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            name = str(entry.get("name") or entry.get("id") or "artifact")
            digest = str(entry.get("digest") or entry.get("hash") or "")
            if digest:
                rows.append(
                    {
                        "name": name,
                        "digest": digest,
                        "algorithm": str(entry.get("algorithm") or "sha256"),
                        "source_artifact": str(artifact.get("id") or field),
                    }
                )
    for key in ("trace_hash", "policy_hash", "events_hash", "spec_hash"):
        val = artifact.get(key)
        if isinstance(val, str) and val.strip():
            rows.append(
                {
                    "name": key,
                    "digest": val.strip(),
                    "algorithm": "sha256",
                    "source_artifact": str(artifact.get("id") or "metadata"),
                }
            )
    return rows


def _source_metadata(artifact: dict[str, Any] | None) -> dict[str, str]:
    if not isinstance(artifact, dict):
        return {"source_repo": "", "source_commit": ""}
    return {
        "source_repo": str(artifact.get("source_repo") or ""),
        "source_commit": str(artifact.get("source_commit") or ""),
    }


def normalize_signed_bundle(bundle: dict[str, Any]) -> dict[str, Any]:
    """Build durable portal read model from a signed ScienceClaimBundle."""
    scb = bundle["science_claim_bundle"]
    claim = scb["claim"]
    claim_id = str(claim["id"])

    vr = bundle.get("verification_result")
    if vr is None:
        vr = scb.get("verification_result")

    assumption_set = scb.get("assumption_set") or {}
    runtime_receipt = scb.get("runtime_receipt") or {}
    trace_certificate = scb.get("trace_certificate") or {}

    hash_artifacts = [claim, assumption_set, runtime_receipt, trace_certificate]
    if isinstance(vr, dict):
        hash_artifacts.append(vr)
    evidence = scb.get("evidence_bundle")
    if isinstance(evidence, dict):
        hash_artifacts.append(evidence)

    artifact_hashes: list[dict[str, str]] = []
    for art in hash_artifacts:
        artifact_hashes.extend(_hash_rows(art if isinstance(art, dict) else None))

    sources: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for art in hash_artifacts:
        if not isinstance(art, dict):
            continue
        meta = _source_metadata(art)
        key = (meta["source_repo"], meta["source_commit"])
        if key in seen or not meta["source_repo"]:
            continue
        seen.add(key)
        sources.append(meta)

    reproduce = list(bundle.get("reproduce_commands") or scb.get("reproduce_commands") or [])
    verify = list(bundle.get("verify_commands") or scb.get("verify_commands") or [])

    limitations = list(scb.get("limitations") or [])
    if LIMITATION_NOTICE not in limitations:
        limitations = [LIMITATION_NOTICE, *limitations]

    guarantee_types = claim.get("guarantee_types")
    if not isinstance(guarantee_types, dict):
        guarantee_types = {k: False for k in GUARANTEE_KEYS}
        guarantee_types["runtime_observed"] = str(runtime_receipt.get("status")) in (
            "RuntimeObserved",
            "RuntimeChecked",
        )
        guarantee_types["certificate_checked"] = str(trace_certificate.get("status")) == (
            "CertificateChecked"
        )
        if isinstance(vr, dict):
            for check in vr.get("checks") or []:
                if not isinstance(check, dict):
                    continue
                gt = str(check.get("guarantee_type") or "")
                if gt in GUARANTEE_KEYS and check.get("outcome") == "pass":
                    guarantee_types[gt] = True

    return {
        "schema_version": "PcsClaimReadModel.v0",
        "claim_id": claim_id,
        "claim": {
            "id": claim_id,
            "text": str(claim.get("claim_text") or ""),
            "status": str(claim.get("status") or ""),
            "signature_or_digest": str(claim.get("signature_or_digest") or ""),
            "guarantee_types": guarantee_types,
            **{k: claim.get(k) for k in ("producer", "producer_version", "created_at")},
        },
        "assumption_set": assumption_set,
        "runtime_receipt": runtime_receipt,
        "trace_certificate": trace_certificate,
        "verification_result": vr,
        "artifact_hashes": artifact_hashes,
        "source_repositories": sources,
        "reproduce_commands": reproduce,
        "verify_commands": verify,
        "limitations": limitations,
        "limitation_notice": LIMITATION_NOTICE,
        "bundle_signature_or_digest": str(bundle.get("signature_or_digest") or ""),
    }
