"""Normalize PCS nested artifacts into a portal read model."""

from __future__ import annotations

import json
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
    "This artifact is a proof-carrying scientific release. It demonstrates "
    "protocol-level validation and runtime evidence for the cited workflow. It is "
    "not production certification, clinical validation, or a guarantee about "
    "real-world deployment outside the stated workflow profile."
)

_CHECK_OUTCOME_MAP = {
    "passed": "pass",
    "failed": "fail",
    "skipped": "skip",
    "warning": "warn",
    "pass": "pass",
    "fail": "fail",
    "skip": "skip",
    "warn": "warn",
}


def _artifact_id(artifact: dict[str, Any]) -> str:
    for key in (
        "id",
        "artifact_id",
        "receipt_id",
        "certificate_id",
        "assumption_set_id",
        "bundle_id",
        "verification_id",
    ):
        val = artifact.get(key)
        if isinstance(val, str) and val.strip():
            return val.strip()
    return ""


def _get_claim(scb: dict[str, Any]) -> dict[str, Any]:
    claim = scb.get("claim_artifact") or scb.get("claim")
    return claim if isinstance(claim, dict) else {}


def _get_runtime_receipt(scb: dict[str, Any]) -> dict[str, Any]:
    receipt = scb.get("runtime_receipt")
    if isinstance(receipt, dict):
        return receipt
    receipts = scb.get("runtime_receipts")
    if isinstance(receipts, list) and receipts and isinstance(receipts[0], dict):
        return receipts[0]
    return {}


def _get_trace_certificate(scb: dict[str, Any]) -> dict[str, Any]:
    cert = scb.get("trace_certificate")
    if isinstance(cert, dict):
        return cert
    certificates = scb.get("certificates")
    if isinstance(certificates, list) and certificates and isinstance(certificates[0], dict):
        return certificates[0]
    return {}


def _normalize_assumption(raw: dict[str, Any]) -> dict[str, str]:
    return {
        "id": str(raw.get("id") or raw.get("assumption_id") or ""),
        "text": str(raw.get("text") or ""),
        "kind": str(raw.get("kind") or "") or None,
        "status": str(raw.get("status") or "") or None,
    }


def _normalize_assumption_set(raw: dict[str, Any]) -> dict[str, Any]:
    assumptions = raw.get("assumptions")
    normalized_assumptions: list[dict[str, str | None]] = []
    if isinstance(assumptions, list):
        for item in assumptions:
            if isinstance(item, dict):
                normalized_assumptions.append(_normalize_assumption(item))
    out = dict(raw)
    out["id"] = _artifact_id(raw) or out.get("id", "")
    out["assumptions"] = normalized_assumptions
    return out


def _normalize_named_artifact(raw: dict[str, Any]) -> dict[str, Any]:
    out = dict(raw)
    aid = _artifact_id(raw)
    if aid:
        out["id"] = aid
    return out


def _hash_rows_from_list_entries(artifact: dict[str, Any]) -> list[dict[str, str]]:
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
                        "source_artifact": str(artifact.get("id") or _artifact_id(artifact) or field),
                    }
                )
    return rows


def _hash_rows_from_map_entries(artifact: dict[str, Any]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for field in ("input_hashes", "output_hashes", "artifact_hashes"):
        entries = artifact.get(field)
        if not isinstance(entries, dict):
            continue
        for name, digest in entries.items():
            if isinstance(digest, str) and digest.strip():
                rows.append(
                    {
                        "name": str(name),
                        "digest": digest.strip(),
                        "algorithm": "sha256",
                        "source_artifact": str(artifact.get("id") or _artifact_id(artifact) or field),
                    }
                )
    return rows


def _hash_rows(artifact: dict[str, Any] | None) -> list[dict[str, str]]:
    if not isinstance(artifact, dict):
        return []
    rows = _hash_rows_from_list_entries(artifact) + _hash_rows_from_map_entries(artifact)
    for key in ("trace_hash", "policy_hash", "events_hash", "spec_hash"):
        val = artifact.get(key)
        if isinstance(val, str) and val.strip():
            rows.append(
                {
                    "name": key,
                    "digest": val.strip(),
                    "algorithm": "sha256",
                    "source_artifact": str(artifact.get("id") or _artifact_id(artifact) or "metadata"),
                }
            )
    sig = artifact.get("signature_or_digest")
    if isinstance(sig, str) and sig.strip():
        rows.append(
            {
                "name": "signature_or_digest",
                "digest": sig.strip(),
                "algorithm": "sha256",
                "source_artifact": str(artifact.get("id") or _artifact_id(artifact) or "artifact"),
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


def _normalize_verification_result(vr: dict[str, Any] | None) -> dict[str, Any] | None:
    if not isinstance(vr, dict):
        return None
    checks_out: list[dict[str, str]] = []
    for check in vr.get("checks") or []:
        if not isinstance(check, dict):
            continue
        raw_outcome = check.get("outcome") or check.get("status") or ""
        outcome = _CHECK_OUTCOME_MAP.get(str(raw_outcome).lower(), str(raw_outcome))
        details = check.get("details")
        detail_text = check.get("detail")
        if detail_text is None and isinstance(details, dict):
            detail_text = json.dumps(details, sort_keys=True)
        elif detail_text is None and details is not None:
            detail_text = str(details)
        checks_out.append(
            {
                "id": str(check.get("id") or check.get("check_id") or ""),
                "name": str(check.get("name") or check.get("description") or ""),
                "outcome": outcome,
                "detail": str(detail_text or ""),
                "guarantee_type": str(check.get("guarantee_type") or "") or None,
            }
        )
    overall = vr.get("overall_outcome")
    if overall is None and vr.get("status"):
        status = str(vr["status"])
        if status in ("ProofChecked", "CertificateChecked", "RuntimeChecked"):
            overall = "pass"
    return {
        "verification_id": str(
            vr.get("verification_id") or _artifact_id(vr) or vr.get("id") or ""
        ),
        "id": str(vr.get("verification_id") or _artifact_id(vr) or vr.get("id") or ""),
        "status": str(vr.get("status") or ""),
        "verifier": str(vr.get("verifier") or vr.get("producer") or ""),
        "verifier_version": str(
            vr.get("verifier_version") or vr.get("producer_version") or ""
        ),
        "overall_outcome": overall,
        "signature_or_digest": str(vr.get("signature_or_digest") or ""),
        "source_repo": str(vr.get("source_repo") or ""),
        "source_commit": str(vr.get("source_commit") or ""),
        "checks": checks_out,
    }


def _infer_guarantee_types(
    claim: dict[str, Any],
    runtime_receipt: dict[str, Any],
    trace_certificate: dict[str, Any],
    verification_result: dict[str, Any] | None,
) -> dict[str, bool]:
    guarantee_types = claim.get("guarantee_types")
    if isinstance(guarantee_types, dict):
        return {k: bool(guarantee_types.get(k)) for k in GUARANTEE_KEYS}

    inferred = {k: False for k in GUARANTEE_KEYS}
    runtime_status = str(runtime_receipt.get("status") or "")
    inferred["runtime_observed"] = runtime_status in ("RuntimeObserved", "RuntimeChecked")
    inferred["certificate_checked"] = str(trace_certificate.get("status") or "") == (
        "CertificateChecked"
    )
    if isinstance(verification_result, dict):
        for check in verification_result.get("checks") or []:
            if not isinstance(check, dict):
                continue
            gt = str(check.get("guarantee_type") or "")
            outcome = str(check.get("outcome") or "")
            if gt in GUARANTEE_KEYS and outcome == "pass":
                inferred[gt] = True
            if outcome == "pass" and gt == "formally_checked":
                inferred["formally_checked"] = True
    return inferred


def normalize_signed_bundle(bundle: dict[str, Any]) -> dict[str, Any]:
    """Build durable portal read model from a signed ScienceClaimBundle."""
    scb = bundle["science_claim_bundle"]
    claim_raw = _get_claim(scb)
    claim_id = _artifact_id(claim_raw)

    vr_raw = bundle.get("verification_result")
    if vr_raw is None:
        vr_raw = scb.get("verification_result")
    verification_result = _normalize_verification_result(
        vr_raw if isinstance(vr_raw, dict) else None
    )

    assumption_set = _normalize_assumption_set(
        scb.get("assumption_set") if isinstance(scb.get("assumption_set"), dict) else {}
    )
    runtime_receipt = _normalize_named_artifact(_get_runtime_receipt(scb))
    trace_certificate = _normalize_named_artifact(_get_trace_certificate(scb))

    hash_artifacts: list[dict[str, Any]] = [claim_raw, assumption_set, runtime_receipt, trace_certificate]
    if isinstance(vr_raw, dict):
        hash_artifacts.append(vr_raw)
    evidence = scb.get("evidence_bundle")
    if isinstance(evidence, dict):
        hash_artifacts.append(evidence)

    artifact_hashes: list[dict[str, str]] = []
    for art in hash_artifacts:
        artifact_hashes.extend(_hash_rows(art))

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
    if not verify:
        verify = [
            "pf verify science-claim signed_science_claim_bundle.json",
            "just pcs-validate-bundle BUNDLE=signed_science_claim_bundle.json",
        ]

    limitations = list(scb.get("limitations") or [])
    if LIMITATION_NOTICE not in limitations:
        limitations = [LIMITATION_NOTICE, *limitations]

    guarantee_types = _infer_guarantee_types(
        claim_raw, runtime_receipt, trace_certificate, verification_result
    )

    evidence_raw = scb.get("evidence_bundle")
    evidence_bundle = (
        _normalize_named_artifact(evidence_raw) if isinstance(evidence_raw, dict) else {}
    )
    evidence_digest = ""
    if isinstance(evidence_raw, dict):
        evidence_digest = str(evidence_raw.get("signature_or_digest") or "")
        if not evidence_digest:
            ah = evidence_raw.get("artifact_hashes")
            if isinstance(ah, dict) and ah:
                evidence_digest = str(next(iter(ah.values())))

    canonical_digests = {
        "claim_artifact": str(claim_raw.get("signature_or_digest") or ""),
        "runtime_receipt": str(runtime_receipt.get("signature_or_digest") or ""),
        "trace_certificate": str(trace_certificate.get("signature_or_digest") or ""),
        "evidence_bundle": evidence_digest,
        "signed_bundle": str(
            bundle.get("signature_or_digest") or bundle.get("bundle_digest") or ""
        ),
    }
    for role, digest in canonical_digests.items():
        if digest:
            artifact_hashes.append(
                {
                    "name": role,
                    "digest": digest,
                    "algorithm": "sha256",
                    "source_artifact": role,
                }
            )

    return {
        "schema_version": "PcsClaimReadModel.v0",
        "claim_id": claim_id,
        "claim": {
            "id": claim_id,
            "text": str(claim_raw.get("claim_text") or ""),
            "status": str(claim_raw.get("status") or ""),
            "signature_or_digest": str(claim_raw.get("signature_or_digest") or ""),
            "guarantee_types": guarantee_types,
            **{k: claim_raw.get(k) for k in ("producer", "producer_version", "created_at")},
        },
        "assumption_set": assumption_set,
        "runtime_receipt": runtime_receipt,
        "trace_certificate": trace_certificate,
        "evidence_bundle": evidence_bundle,
        "verification_result": verification_result,
        "artifact_hashes": artifact_hashes,
        "canonical_digests": canonical_digests,
        "source_repositories": sources,
        "reproduce_commands": reproduce,
        "verify_commands": verify,
        "limitations": limitations,
        "limitation_notice": LIMITATION_NOTICE,
        "bundle_signature_or_digest": str(
            bundle.get("signature_or_digest") or bundle.get("bundle_digest") or ""
        ),
    }
