"""Map registry rows to admission status labels for portal rendering."""

from __future__ import annotations

from typing import Any

ADMISSION_PASSED = "passed"
ADMISSION_WARNING = "warning"
ADMISSION_FAILED = "failed"
ADMISSION_DEFERRED = "deferred"
ADMISSION_NOT_APPLICABLE = "not_applicable"


def _checks_failed_for_artifact(checks: list[str]) -> bool:
    for label in checks:
        lowered = label.lower()
        if "fail" in lowered or "reject" in lowered or "mismatch" in lowered:
            return True
    return False


def compute_registry_admission_status(
    row: dict[str, Any],
    *,
    checks_for_artifact: list[str] | None = None,
) -> str:
    checks = checks_for_artifact or []
    artifact_type = str(row.get("artifact_type") or "").strip()
    if not artifact_type:
        return ADMISSION_NOT_APPLICABLE

    missing = row.get("required_release_fields_missing") or []
    admission = str(row.get("registry_admission_result") or "")

    if _checks_failed_for_artifact(checks):
        return ADMISSION_FAILED
    if missing:
        return ADMISSION_FAILED
    if admission == "incomplete":
        return ADMISSION_WARNING
    if admission == "admitted":
        if checks and not _checks_failed_for_artifact(checks):
            return ADMISSION_PASSED
        return ADMISSION_PASSED if not checks else ADMISSION_WARNING
    return ADMISSION_DEFERRED


def enrich_registry_row(row: dict[str, Any], *, checks_for_artifact: list[str] | None = None) -> dict[str, Any]:
    out = dict(row)
    spec = row  # row already merged with spec fields
    allowed_runtime = spec.get("allowed_runtime_producers")
    if not isinstance(allowed_runtime, list):
        allowed_runtime = []
        runtime = spec.get("runtime_producer")
        if isinstance(runtime, str) and runtime:
            allowed_runtime = [runtime]
    out["allowed_runtime_producers"] = allowed_runtime
    out["admission_status"] = compute_registry_admission_status(
        out,
        checks_for_artifact=checks_for_artifact,
    )
    return out
