"""Formal trust kernel artifacts (ProofObligation.v0, LeanCheckResult.v0) for PCS read models."""

from __future__ import annotations

from typing import Any

FORMAL_TRUST_WORKFLOW_FLAG = "formal_trust_required"
FORMAL_TRUST_SUPPLEMENTAL_TYPES = frozenset(
    {
        "ProofObligation.v0",
        "LeanCheckResult.v0",
    },
)

PROOF_OBLIGATION_FILENAMES = ("proof_obligation.v0.json", "ProofObligation.v0.json")
LEAN_CHECK_RESULT_FILENAMES = ("lean_check_result.v0.json", "LeanCheckResult.v0.json")
LEGACY_FORMAL_TRUST_ARTIFACTS = (
    "proof_obligation.v0.json",
    "lean_check_result.v0.json",
)


def strip_formal_trust_from_legacy_manifest(legacy: dict[str, Any]) -> bool:
    """Remove formal-trust digests from RELEASE_FIXTURE_MANIFEST (pcs-core chain scope)."""
    artifacts = legacy.get("artifacts")
    if not isinstance(artifacts, dict):
        return False
    changed = False
    for name in LEGACY_FORMAL_TRUST_ARTIFACTS:
        if name in artifacts:
            del artifacts[name]
            changed = True
    return changed

FORMAL_NON_CLAIMS = (
    "The Lean check does not prove the scientific claim is true.",
    "The Lean check does not prove the dataset is unbiased.",
    "The Lean check does not prove the model is valid.",
    "The Lean check proves only the declared PCS trust-envelope invariant.",
)

FORMAL_SCOPE_DEFAULT = (
    "Formalization covers PCS trust-envelope predicates in the Lean trust kernel "
    "(certificate/runtime alignment, PF verification admission, and signed-bundle hash binding). "
    "Scientific domain semantics, data quality, and model validity are out of scope."
)

MILESTONE_THEOREMS = (
    {
        "obligation_id": "obl-certificate-matches-runtime",
        "predicate": "CertificateMatchesRuntime",
        "lean_theorem": "PCS.CertificateMatchesRuntime",
        "trust_boundary_invariant": (
            "The temporal certificate trace hash matches the runtime receipt trace hash "
            "and the certificate is CertificateChecked."
        ),
        "source_artifacts": ("trace_certificate.json", "runtime_receipt.json"),
    },
    {
        "obligation_id": "obl-verification-admits-bundle",
        "predicate": "VerificationAdmitsBundle",
        "lean_theorem": "PCS.VerificationAdmitsBundle",
        "trust_boundary_invariant": (
            "Provability Fabric verification is ProofChecked and admits the certified bundle hash."
        ),
        "source_artifacts": ("verification_result.json", "science_claim_bundle.certified.json"),
    },
    {
        "obligation_id": "obl-signed-bundle-admissible",
        "predicate": "SignedBundleAdmissible",
        "lean_theorem": "PCS.SignedBundleAdmissible",
        "trust_boundary_invariant": (
            "The signed bundle input hash matches the PF verified certified bundle hash."
        ),
        "source_artifacts": (
            "signed_science_claim_bundle.json",
            "science_claim_bundle.certified.json",
        ),
    },
    {
        "obligation_id": "obl-rejected-certificate-not-admissible",
        "predicate": "RejectedCertificateNotAdmissible",
        "lean_theorem": "PCS.RejectedCertificateNotAdmissible",
        "trust_boundary_invariant": (
            "A Rejected temporal certificate cannot satisfy an admissible release chain."
        ),
        "source_artifacts": ("trace_certificate.json",),
    },
    {
        "obligation_id": "obl-stale-certificate-not-admissible",
        "predicate": "StaleCertificateNotAdmissible",
        "lean_theorem": "PCS.StaleCertificateNotAdmissible",
        "trust_boundary_invariant": (
            "A Stale temporal certificate cannot satisfy an admissible release chain."
        ),
        "source_artifacts": ("trace_certificate.json",),
    },
)


def _vendored_workflow_profile(workflow_profile_id: str, repo_root: Path) -> dict[str, Any] | None:
    vendored = repo_root / "schemas" / "pcs" / "workflow_profiles"
    if not vendored.is_dir():
        return None
    import json

    for path in sorted(vendored.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8-sig"))
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(data, dict) and data.get("workflow_id") == workflow_profile_id:
            return data
    return None


def workflow_requires_formal_trust(
    profile: dict[str, Any] | None,
    *,
    workflow_profile_id: str | None = None,
    repo_root: Path | None = None,
) -> bool:
    candidates: list[dict[str, Any]] = []
    if isinstance(profile, dict):
        candidates.append(profile)
    if workflow_profile_id and repo_root is not None:
        vendored = _vendored_workflow_profile(workflow_profile_id, repo_root.resolve())
        if isinstance(vendored, dict):
            candidates.append(vendored)

    for candidate in candidates:
        if candidate.get(FORMAL_TRUST_WORKFLOW_FLAG) is True:
            return True
        artifacts = candidate.get("formal_trust_artifacts")
        if isinstance(artifacts, list) and artifacts:
            return True
    return False


def _payload(row: dict[str, Any]) -> dict[str, Any]:
    payload = row.get("payload")
    return payload if isinstance(payload, dict) else {}


def _obligation_rows(supplemental: list[dict[str, Any]]) -> list[dict[str, Any]]:
    for row in supplemental:
        if str(row.get("artifact_type") or "") == "ProofObligation.v0":
            payload = _payload(row)
            obligations = payload.get("obligations")
            if isinstance(obligations, list):
                return [item for item in obligations if isinstance(item, dict)]
    return []


def _lean_result_rows(supplemental: list[dict[str, Any]]) -> list[dict[str, Any]]:
    for row in supplemental:
        if str(row.get("artifact_type") or "") == "LeanCheckResult.v0":
            payload = _payload(row)
            results = payload.get("results")
            if isinstance(results, list):
                return [item for item in results if isinstance(item, dict)]
    return []


def build_formal_check_view(entry: dict[str, Any]) -> dict[str, Any]:
    return {
        "obligation_id": entry.get("obligation_id"),
        "predicate": entry.get("predicate"),
        "lean_theorem": entry.get("lean_theorem"),
        "status": entry.get("status"),
        "source_artifacts": list(entry.get("source_artifacts") or []),
        "checked_at": entry.get("checked_at"),
        "lean_version": entry.get("lean_version"),
        "result": entry.get("result"),
        "trust_boundary_invariant": entry.get("trust_boundary_invariant"),
        "formal_scope": entry.get("formal_scope"),
        "expected": entry.get("expected"),
        "actual": entry.get("actual"),
        "responsible_component": entry.get("responsible_component"),
        "repair_hint": entry.get("repair_hint"),
        "pf_explain": entry.get("pf_explain"),
    }


def build_formal_trust_kernel_view(
    supplemental: list[dict[str, Any]],
) -> dict[str, Any] | None:
    obligation_doc: dict[str, Any] | None = None
    lean_doc: dict[str, Any] | None = None
    for row in supplemental:
        artifact_type = str(row.get("artifact_type") or "")
        if artifact_type == "ProofObligation.v0":
            obligation_doc = _payload(row)
        elif artifact_type == "LeanCheckResult.v0":
            lean_doc = _payload(row)

    if obligation_doc is None and lean_doc is None:
        return None

    obligations = _obligation_rows(supplemental)
    obligation_by_id = {
        str(item.get("obligation_id")): item for item in obligations if item.get("obligation_id")
    }
    lean_results = _lean_result_rows(supplemental)

    proof_obligations: list[dict[str, Any]] = []
    for item in obligations:
        proof_obligations.append(build_formal_check_view(item))

    lean_check_results: list[dict[str, Any]] = []
    for item in lean_results:
        merged = dict(obligation_by_id.get(str(item.get("obligation_id") or ""), {}))
        merged.update(item)
        lean_check_results.append(build_formal_check_view(merged))

    theorems = sorted(
        {
            str(item.get("lean_theorem"))
            for item in lean_check_results
            if item.get("lean_theorem")
        },
    )
    artifacts_used = sorted(
        {
            name
            for item in lean_check_results
            for name in item.get("source_artifacts") or []
            if isinstance(name, str)
        },
    )
    invariants = [
        str(item.get("trust_boundary_invariant"))
        for item in proof_obligations
        if item.get("trust_boundary_invariant")
    ]

    overall_status = str((lean_doc or {}).get("status") or "")
    return {
        "title": "Formal Trust Kernel",
        "release_id": (lean_doc or obligation_doc or {}).get("release_id"),
        "obligation_set_id": (obligation_doc or {}).get("obligation_set_id")
        or (lean_doc or {}).get("obligation_set_id"),
        "overall_status": overall_status,
        "lean_version": (lean_doc or {}).get("lean_version"),
        "checked_at": (lean_doc or {}).get("checked_at"),
        "checker": (lean_doc or {}).get("checker"),
        "checker_version": (lean_doc or {}).get("checker_version"),
        "trust_boundary": (obligation_doc or {}).get("trust_boundary"),
        "what_was_checked": (
            "Lean-checked PCS trust-envelope obligations for this release: "
            + ", ".join(theorems)
            if theorems
            else "Lean-checked PCS trust-envelope obligations for this release."
        ),
        "trust_boundary_invariants": invariants,
        "artifacts_used": artifacts_used,
        "theorems_checked": theorems,
        "proof_obligations": proof_obligations,
        "lean_check_results": lean_check_results,
        "formal_scope": (obligation_doc or {}).get("formal_scope") or FORMAL_SCOPE_DEFAULT,
        "formal_non_claims": list(FORMAL_NON_CLAIMS),
        "pf_explain": (lean_doc or {}).get("pf_explain"),
    }


def formal_trust_lineage_from_supplemental(
    supplemental: list[dict[str, Any]],
) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for row in supplemental:
        artifact_type = str(row.get("artifact_type") or "")
        payload = _payload(row)
        if artifact_type == "ProofObligation.v0":
            out["obligation_set_id"] = payload.get("obligation_set_id")
        elif artifact_type == "LeanCheckResult.v0":
            out["lean_check_status"] = payload.get("status")
            out["lean_check_result_id"] = payload.get("check_result_id")
            theorems = {
                str(item.get("lean_theorem"))
                for item in payload.get("results") or []
                if isinstance(item, dict) and item.get("lean_theorem")
            }
            if theorems:
                out["lean_theorems"] = sorted(theorems)
            failed = [
                str(item.get("lean_theorem"))
                for item in payload.get("results") or []
                if isinstance(item, dict) and item.get("result") == "failed"
            ]
            if failed:
                out["failed_lean_theorems"] = sorted(failed)
    return {key: value for key, value in out.items() if value not in (None, "", [])}


def attach_formal_trust_artifacts(
    read_model: dict[str, Any],
    supplemental: list[dict[str, Any]],
) -> dict[str, Any]:
    from sm_pipeline.pcs_import.supplemental_protocol import protocol_artifact_to_named

    out = dict(read_model)
    kernel = build_formal_trust_kernel_view(supplemental)
    if kernel is not None:
        out["formal_trust_kernel"] = kernel

    by_type: dict[str, dict[str, Any]] = {}
    for row in supplemental:
        artifact_type = str(row.get("artifact_type") or "")
        if artifact_type in FORMAL_TRUST_SUPPLEMENTAL_TYPES:
            by_type[artifact_type] = row

    if "ProofObligation.v0" in by_type:
        out["proof_obligation"] = protocol_artifact_to_named(by_type["ProofObligation.v0"])
    if "LeanCheckResult.v0" in by_type:
        out["lean_check_result"] = protocol_artifact_to_named(by_type["LeanCheckResult.v0"])

    limitations = list(out.get("limitations") or [])
    for notice in FORMAL_NON_CLAIMS:
        if notice not in limitations:
            limitations.append(notice)
    out["limitations"] = limitations
    return out
