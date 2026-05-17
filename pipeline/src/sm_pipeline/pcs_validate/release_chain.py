"""Atomic PCS v0.1 release-run validation (delegates to pcs-core when installed)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

MANIFEST_NAME = "RELEASE_FIXTURE_MANIFEST.json"
MANIFEST_ARTIFACTS = (
    "trace.json",
    "runtime_receipt.json",
    "trace_certificate.json",
    "science_claim_bundle.pending.json",
    "science_claim_bundle.certified.json",
    "verification_result.json",
    "signed_science_claim_bundle.json",
    "scientific_memory_import_report.json",
)


@dataclass(frozen=True)
class ReleaseChainIssue:
    code: str
    message: str

    def format(self) -> str:
        return f"{self.code}: {self.message}"


def _load_json(path: Path) -> dict[str, Any] | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError:
        return None
    return data if isinstance(data, dict) else None


def _first_certificate_id(bundle: dict[str, Any]) -> str | None:
    certs = bundle.get("certificates")
    if not isinstance(certs, list) or not certs or not isinstance(certs[0], dict):
        return None
    cid = certs[0].get("certificate_id")
    return cid if isinstance(cid, str) else None


def _vr_certificate_refs(vr: dict[str, Any]) -> list[str]:
    checks = vr.get("checks")
    if not isinstance(checks, list):
        return []
    for check in checks:
        if not isinstance(check, dict) or check.get("check_id") != "evidence_refs_complete":
            continue
        details = check.get("details")
        if isinstance(details, dict):
            refs = details.get("certificate_refs")
            if isinstance(refs, list):
                return [r for r in refs if isinstance(r, str)]
    return []


def validate_release_chain(directory: Path) -> list[ReleaseChainIssue]:
    """Validate release-run atomic consistency."""
    try:
        from pcs_core.release_chain import validate_release_chain as _pcs_validate

        return [
            ReleaseChainIssue(code=issue.code, message=issue.message)
            for issue in _pcs_validate(directory)
        ]
    except (ImportError, SyntaxError):
        return _validate_release_chain_fallback(directory)


def validate_release_chain_messages(directory: Path) -> list[str]:
    return [issue.format() for issue in validate_release_chain(directory)]


def _validate_release_chain_fallback(directory: Path) -> list[ReleaseChainIssue]:
    """Minimal release-chain checks when pcs-core is not installed."""
    issues: list[ReleaseChainIssue] = []
    base = directory.resolve()
    manifest = _load_json(base / MANIFEST_NAME)
    if manifest is None:
        return [ReleaseChainIssue("missing_manifest", f"{MANIFEST_NAME} not found")]

    certified = _load_json(base / "science_claim_bundle.certified.json")
    signed = _load_json(base / "signed_science_claim_bundle.json")
    verification = _load_json(base / "verification_result.json")
    sm_report = _load_json(base / "scientific_memory_import_report.json")
    trace_cert = _load_json(base / "trace_certificate.json")

    if certified and signed:
        scb = signed.get("science_claim_bundle")
        if isinstance(scb, dict) and certified.get("bundle_id") != scb.get("bundle_id"):
            issues.append(
                ReleaseChainIssue(
                    "mixed_run_certificate_id",
                    "signed.science_claim_bundle.bundle_id != certified bundle_id",
                )
            )
        cert_certified = _first_certificate_id(certified)
        cert_signed = _first_certificate_id(scb) if isinstance(scb, dict) else None
        if cert_certified and cert_signed and cert_certified != cert_signed:
            issues.append(
                ReleaseChainIssue(
                    "mixed_run_certificate_id",
                    f"certified certificate_id {cert_certified} != signed {cert_signed}",
                )
            )

    cert_ids: dict[str, str] = {}
    if trace_cert and isinstance(trace_cert.get("certificate_id"), str):
        cert_ids["trace_certificate.json"] = trace_cert["certificate_id"]
    if certified:
        cid = _first_certificate_id(certified)
        if cid:
            cert_ids["science_claim_bundle.certified.json"] = cid
    if verification:
        refs = _vr_certificate_refs(verification)
        if refs:
            cert_ids["verification_result.json"] = refs[0]
    if signed and isinstance(signed.get("science_claim_bundle"), dict):
        cid = _first_certificate_id(signed["science_claim_bundle"])
        if cid:
            cert_ids["signed_science_claim_bundle.json"] = cid

    unique = {v for v in cert_ids.values()}
    if len(unique) > 1:
        issues.append(
            ReleaseChainIssue(
                "mixed_run_certificate_id",
                f"certificate_id mismatch: {cert_ids}",
            )
        )

    if verification and verification.get("status") != "ProofChecked":
        issues.append(
            ReleaseChainIssue(
                "mixed_run_pf_verification_result",
                "verification_result.status must be ProofChecked",
            )
        )
    if signed:
        vr = signed.get("verification_result")
        if isinstance(vr, dict) and vr.get("status") != "ProofChecked":
            issues.append(
                ReleaseChainIssue(
                    "mixed_run_pf_verification_result",
                    "signed.verification_result.status must be ProofChecked",
                )
            )

    if sm_report and sm_report.get("verification_status") != "passed":
        issues.append(
            ReleaseChainIssue(
                "invalid_artifact",
                "scientific_memory_import_report.verification_status must be passed",
            )
        )

    pf_commit = manifest.get("provability_fabric_commit")
    if isinstance(pf_commit, str) and signed:
        vr = signed.get("verification_result")
        if isinstance(vr, dict) and vr.get("source_commit") != pf_commit:
            issues.append(
                ReleaseChainIssue(
                    "manifest_commit_mismatch",
                    "signed.verification_result.source_commit != provability_fabric_commit",
                )
            )
        if signed.get("source_commit") != pf_commit:
            issues.append(
                ReleaseChainIssue(
                    "manifest_commit_mismatch",
                    "signed_bundle.source_commit != provability_fabric_commit",
                )
            )

    return issues
