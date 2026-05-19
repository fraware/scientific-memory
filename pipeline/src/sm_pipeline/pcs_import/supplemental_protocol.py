"""Load release-dir protocol artifacts not embedded in SignedScienceClaimBundle."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from sm_pipeline.pcs_validate.canonical_hash import file_sha256_digest

from sm_pipeline.pcs_import.computation_protocol import COMPUTATION_SUPPLEMENTAL_TYPES
from sm_pipeline.pcs_import.formal_trust_protocol import FORMAL_TRUST_SUPPLEMENTAL_TYPES

SUPPLEMENTAL_ARTIFACT_TYPES = frozenset(
    {
        "ToolUseTrace.v0",
        "ToolUseCertificate.v0",
        "WorkflowProfile.v0",
        *COMPUTATION_SUPPLEMENTAL_TYPES,
        *FORMAL_TRUST_SUPPLEMENTAL_TYPES,
    },
)

STANDARD_BUNDLE_TYPES = frozenset(
    {
        "RuntimeReceipt.v0",
        "TraceCertificate.v0",
        "ScienceClaimBundle.v0",
        "SignedScienceClaimBundle.v0",
        "VerificationResult.v0",
        "ClaimArtifact.v0",
        "AssumptionSet.v0",
        "EvidenceBundle.v0",
    },
)


def _load_json(path: Path) -> dict[str, Any] | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except (json.JSONDecodeError, OSError):
        return None
    return data if isinstance(data, dict) else None


def _artifact_id(data: dict[str, Any]) -> str:
    for key in (
        "trace_id",
        "certificate_id",
        "witness_id",
        "obligation_set_id",
        "check_result_id",
        "dataset_id",
        "environment_id",
        "run_id",
        "result_id",
        "workflow_id",
        "id",
        "artifact_id",
    ):
        val = data.get(key)
        if isinstance(val, str) and val.strip():
            return val.strip()
    return ""


def build_supplemental_protocol_artifact(
    *,
    name: str,
    artifact_type: str,
    path: Path,
    manifest_entry: dict[str, Any] | None = None,
) -> dict[str, Any]:
    data = _load_json(path)
    entry = manifest_entry if isinstance(manifest_entry, dict) else {}
    digest = file_sha256_digest(path) if path.is_file() else str(entry.get("sha256") or "")
    return {
        "name": name,
        "artifact_type": artifact_type,
        "id": _artifact_id(data or {}),
        "schema_version": (data or {}).get("schema_version") or entry.get("schema_version"),
        "status": (data or {}).get("status") or entry.get("status"),
        "source_repo": (data or {}).get("source_repo") or entry.get("source_repo"),
        "source_commit": (data or {}).get("source_commit") or entry.get("source_commit"),
        "hash": digest,
        "signature_or_digest": (data or {}).get("signature_or_digest"),
        "path": str(path),
        "payload": data,
    }


def load_supplemental_protocol_artifacts(
    manifest: dict[str, Any],
    release_dir: Path,
) -> list[dict[str, Any]]:
    """Artifacts listed in ReleaseManifest.v0 outside the standard claim bundle."""
    artifacts = manifest.get("artifacts")
    if not isinstance(artifacts, dict):
        return []

    supplemental: list[dict[str, Any]] = []
    for name, entry in sorted(artifacts.items()):
        if not isinstance(entry, dict):
            continue
        artifact_type = str(entry.get("artifact_type") or "")
        if artifact_type in STANDARD_BUNDLE_TYPES:
            continue
        if artifact_type not in SUPPLEMENTAL_ARTIFACT_TYPES:
            continue
        path = release_dir / name
        if not path.is_file():
            continue
        supplemental.append(
            build_supplemental_protocol_artifact(
                name=name,
                artifact_type=artifact_type,
                path=path,
                manifest_entry=entry,
            ),
        )
    return supplemental


def supplemental_by_type(
    supplemental: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    indexed: dict[str, dict[str, Any]] = {}
    for row in supplemental:
        artifact_type = str(row.get("artifact_type") or "")
        if artifact_type:
            indexed[artifact_type] = row
    return indexed


def attach_domain_artifacts(read_model: dict[str, Any], supplemental: list[dict[str, Any]]) -> dict[str, Any]:
    """Promote domain protocol artifacts to first-class read-model fields."""
    from sm_pipeline.pcs_import.computation_protocol import attach_computation_artifacts
    from sm_pipeline.pcs_import.formal_trust_protocol import (
        FORMAL_TRUST_SUPPLEMENTAL_TYPES,
        attach_formal_trust_artifacts,
    )

    out = dict(read_model)
    by_type = supplemental_by_type(supplemental)
    trace = by_type.get("ToolUseTrace.v0")
    if trace is not None:
        out["tool_use_trace"] = protocol_artifact_to_named(trace)
    cert = by_type.get("ToolUseCertificate.v0")
    if cert is not None:
        out["tool_use_certificate"] = protocol_artifact_to_named(cert)

    has_computation = any(
        str(row.get("artifact_type") or "") in COMPUTATION_SUPPLEMENTAL_TYPES for row in supplemental
    )
    if has_computation:
        out = attach_computation_artifacts(out, supplemental)

    has_formal = any(
        str(row.get("artifact_type") or "") in FORMAL_TRUST_SUPPLEMENTAL_TYPES for row in supplemental
    )
    if has_formal:
        out = attach_formal_trust_artifacts(out, supplemental)

    promoted_types = {
        "ToolUseTrace.v0",
        "ToolUseCertificate.v0",
        "WorkflowProfile.v0",
        *COMPUTATION_SUPPLEMENTAL_TYPES,
        *FORMAL_TRUST_SUPPLEMENTAL_TYPES,
    }
    if has_computation or has_formal:
        remaining = [
            row
            for row in supplemental
            if str(row.get("artifact_type") or "") not in promoted_types
        ]
        if remaining:
            out["protocol_artifacts"] = remaining
        return out

    remaining = [
        row
        for row in supplemental
        if str(row.get("artifact_type") or "")
        not in {"ToolUseTrace.v0", "ToolUseCertificate.v0", "WorkflowProfile.v0", *FORMAL_TRUST_SUPPLEMENTAL_TYPES}
    ]
    if remaining:
        out["protocol_artifacts"] = remaining
    elif "protocol_artifacts" in out and not remaining:
        out.pop("protocol_artifacts", None)
    return out


def protocol_artifact_to_named(row: dict[str, Any]) -> dict[str, Any]:
    """Map supplemental row to PcsNamedArtifact-compatible shape for portal renderers."""
    payload = row.get("payload") if isinstance(row.get("payload"), dict) else {}
    merged = {**payload, **{k: v for k, v in row.items() if k != "payload"}}
    artifact_id = str(
        row.get("id") or merged.get("trace_id") or merged.get("certificate_id") or "",
    )
    return {
        "id": artifact_id or str(row.get("name") or ""),
        "artifact_type": row.get("artifact_type"),
        "schema_version": row.get("schema_version"),
        "status": row.get("status"),
        "source_repo": row.get("source_repo"),
        "source_commit": row.get("source_commit"),
        "signature_or_digest": row.get("signature_or_digest") or row.get("hash"),
        "summary": str(merged.get("description") or merged.get("workflow_id") or row.get("artifact_type") or ""),
        "payload": payload or merged,
    }
