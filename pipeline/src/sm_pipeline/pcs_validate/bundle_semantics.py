"""Semantic PCS bundle validation (strict import contract; pcs-core is canonical)."""

from __future__ import annotations

from typing import Any

from sm_pipeline.pcs_validate.bundle_detection import detect_bundle_shape, is_legacy_signed_bundle
from sm_pipeline.pcs_validate.placeholder_commits import (
    is_local_dev_marker,
    validate_source_commit_for_release,
)

_CHECK_PASS = frozenset({"pass", "passed", "ok", "success"})
_CHECK_FAIL = frozenset({"fail", "failed", "error", "rejected"})
_VR_SUCCESS_STATUS = frozenset(
    {
        "passed",
        "pass",
        "proofchecked",
        "runtimechecked",
        "certificatechecked",
    }
)
_VR_FAIL_STATUS = frozenset({"failed", "fail", "rejected", "error"})


def _get_scb(bundle: dict[str, Any]) -> dict[str, Any] | None:
    scb = bundle.get("science_claim_bundle")
    return scb if isinstance(scb, dict) else None


def _get_verification_result(bundle: dict[str, Any], scb: dict[str, Any] | None) -> dict[str, Any] | None:
    vr = bundle.get("verification_result")
    if isinstance(vr, dict):
        return vr
    if scb is not None:
        nested = scb.get("verification_result")
        if isinstance(nested, dict):
            return nested
    return None


def _get_claim(scb: dict[str, Any]) -> dict[str, Any] | None:
    claim = scb.get("claim_artifact") or scb.get("claim")
    return claim if isinstance(claim, dict) else None


def _get_assumption_set(scb: dict[str, Any]) -> dict[str, Any] | None:
    assumption_set = scb.get("assumption_set")
    return assumption_set if isinstance(assumption_set, dict) else None


def _get_runtime_receipt(scb: dict[str, Any]) -> dict[str, Any] | None:
    receipt = scb.get("runtime_receipt")
    if isinstance(receipt, dict):
        return receipt
    receipts = scb.get("runtime_receipts")
    if isinstance(receipts, list) and receipts and isinstance(receipts[0], dict):
        return receipts[0]
    return None


def _get_trace_certificate(scb: dict[str, Any]) -> dict[str, Any] | None:
    cert = scb.get("trace_certificate")
    if isinstance(cert, dict):
        return cert
    certificates = scb.get("certificates")
    if isinstance(certificates, list) and certificates and isinstance(certificates[0], dict):
        return certificates[0]
    return None


def _is_signed_bundle(bundle: dict[str, Any]) -> bool:
    return bool(
        str(bundle.get("signature_or_digest") or bundle.get("bundle_digest") or "").strip()
    )


def _check_passed(check: dict[str, Any]) -> bool:
    raw = check.get("outcome") or check.get("status") or ""
    return str(raw).lower() in _CHECK_PASS


def _check_failed(check: dict[str, Any]) -> bool:
    raw = check.get("outcome") or check.get("status") or ""
    return str(raw).lower() in _CHECK_FAIL


def verification_result_passed(vr: dict[str, Any]) -> bool:
    status = str(vr.get("status") or "").lower()
    if status in _VR_FAIL_STATUS:
        return False
    overall = str(vr.get("overall_outcome") or "").lower()
    if overall in _CHECK_FAIL:
        return False
    checks = vr.get("checks")
    if isinstance(checks, list) and checks:
        if any(_check_failed(c) for c in checks if isinstance(c, dict)):
            return False
        if all(_check_passed(c) for c in checks if isinstance(c, dict)):
            return True
    if status in _VR_SUCCESS_STATUS or overall in _CHECK_PASS:
        return True
    if status == "passed":
        return True
    return False


def _require_signature(artifact: dict[str, Any], path: str, errors: list[str]) -> None:
    if not str(artifact.get("signature_or_digest") or "").strip():
        errors.append(f"{path}: signature_or_digest is required")


def _require_source_commit(
    artifact: dict[str, Any],
    path: str,
    errors: list[str],
    *,
    strict: bool,
) -> None:
    commit = str(artifact.get("source_commit") or "").strip()
    if not commit:
        errors.append(f"{path}: source_commit is required")
        return
    if strict:
        local_dev = artifact.get("local_dev")
        msg = validate_source_commit_for_release(
            commit, path=path, local_dev=local_dev
        )
        if msg:
            errors.append(msg)


def _reject_release_local_dev_flags(bundle: dict[str, Any], errors: list[str]) -> None:
    scb = _get_scb(bundle)
    if not isinstance(scb, dict):
        return
    if is_local_dev_marker(scb.get("local_dev")):
        errors.append("science_claim_bundle.local_dev is not allowed for release import")
    for label, artifact in (
        ("signed_bundle", bundle),
        ("verification_result", _get_verification_result(bundle, scb)),
    ):
        if isinstance(artifact, dict) and is_local_dev_marker(artifact.get("local_dev")):
            errors.append(f"{label}.local_dev is not allowed for release import")


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


def _reject_release_trace_hash_consistency(
    scb: dict[str, Any],
    *,
    errors: list[str],
) -> None:
    trace_cert = _get_trace_certificate(scb)
    receipt = _get_runtime_receipt(scb)
    if not isinstance(trace_cert, dict) or not isinstance(receipt, dict):
        return
    cert_hash = trace_cert.get("trace_hash")
    receipt_hash = receipt.get("trace_hash")
    receipt_id = receipt.get("receipt_id") or receipt.get("id") or "runtime_receipt"
    cert_id = trace_cert.get("certificate_id") or trace_cert.get("id") or "certificate"
    if (
        isinstance(cert_hash, str)
        and isinstance(receipt_hash, str)
        and cert_hash != receipt_hash
    ):
        errors.append(
            "trace_hash mismatch: "
            f"receipt {receipt_id} ({receipt_hash}) vs certificate {cert_id} ({cert_hash})"
        )


def _reject_release_certificate_consistency(
    bundle: dict[str, Any],
    scb: dict[str, Any],
    *,
    errors: list[str],
) -> None:
    """Reject when PF verification_result certificate_refs disagree with bundle certificate."""
    vr = _get_verification_result(bundle, scb)
    trace_cert = _get_trace_certificate(scb)
    if not isinstance(vr, dict) or not isinstance(trace_cert, dict):
        return
    cert_id = trace_cert.get("certificate_id")
    if not isinstance(cert_id, str):
        return
    refs = _vr_certificate_refs(vr)
    if refs and refs[0] != cert_id:
        errors.append(
            "verification_result certificate_refs do not match trace certificate_id "
            f"({refs[0]!r} != {cert_id!r})"
        )


def collect_semantic_errors(bundle: dict[str, Any], *, strict: bool) -> list[str]:
    """Return validation errors; empty when bundle satisfies strict import semantics."""
    errors: list[str] = []

    if not _get_scb(bundle):
        errors.append("science_claim_bundle is required")
        return errors

    scb = _get_scb(bundle)
    assert scb is not None

    claim = _get_claim(scb)
    if claim is None:
        errors.append("science_claim_bundle.claim_artifact (or claim) is required")

    assumption_set = _get_assumption_set(scb)
    if assumption_set is None:
        errors.append("science_claim_bundle.assumption_set is required")
    else:
        assumptions = assumption_set.get("assumptions")
        if not isinstance(assumptions, list) or len(assumptions) == 0:
            errors.append("science_claim_bundle.assumption_set.assumptions must be non-empty")

    runtime_receipt = _get_runtime_receipt(scb)
    if runtime_receipt is None:
        errors.append("science_claim_bundle.runtime_receipt (or runtime_receipts) is required")

    trace_cert = _get_trace_certificate(scb)
    if _is_signed_bundle(bundle):
        if trace_cert is None:
            errors.append(
                "signed bundle requires trace_certificate or certificates[0]"
            )
        elif str(trace_cert.get("status") or "") != "CertificateChecked":
            if strict:
                errors.append(
                    f"trace_certificate.status must be CertificateChecked "
                    f"(got {trace_cert.get('status')!r})"
                )

    vr = _get_verification_result(bundle, scb)
    if vr is None:
        if strict:
            errors.append("verification_result is required in strict mode")
    elif not verification_result_passed(vr):
        errors.append("verification_result did not pass (status or checks)")

    if _is_signed_bundle(bundle):
        _require_signature(bundle, "signed_bundle", errors)

    release_strict = strict and detect_bundle_shape(bundle) == "pcs_core"

    if release_strict:
        _reject_release_local_dev_flags(bundle, errors)
        _reject_release_trace_hash_consistency(scb, errors=errors)
        _reject_release_certificate_consistency(bundle, scb, errors=errors)

    for label, artifact in (
        ("science_claim_bundle.claim_artifact", claim),
        ("science_claim_bundle.assumption_set", assumption_set),
        ("science_claim_bundle.runtime_receipt", runtime_receipt),
        ("science_claim_bundle.trace_certificate", trace_cert),
        ("verification_result", vr),
    ):
        if isinstance(artifact, dict):
            _require_source_commit(artifact, label, errors, strict=release_strict)
            _require_signature(artifact, label, errors)

    if isinstance(scb, dict):
        _require_source_commit(scb, "science_claim_bundle", errors, strict=release_strict)
        if is_legacy_signed_bundle({"science_claim_bundle": scb}):
            _require_signature(scb, "science_claim_bundle", errors)

    if release_strict and _is_signed_bundle(bundle):
        _require_source_commit(bundle, "signed_bundle", errors, strict=True)

    return errors


def collect_semantic_warnings(bundle: dict[str, Any]) -> list[str]:
    """Non-fatal warnings when strict=False allows import without verification_result."""
    warnings: list[str] = []
    scb = _get_scb(bundle)
    if scb is None:
        return warnings

    vr = _get_verification_result(bundle, scb)
    if vr is None:
        warnings.append(
            "VerificationResult is absent; import proceeds with advisory only."
        )

    trace_cert = _get_trace_certificate(scb)
    if isinstance(trace_cert, dict):
        status = str(trace_cert.get("status") or "")
        if status != "CertificateChecked":
            warnings.append(
                f"trace_certificate.status is {status!r}, expected CertificateChecked."
            )
    return warnings
