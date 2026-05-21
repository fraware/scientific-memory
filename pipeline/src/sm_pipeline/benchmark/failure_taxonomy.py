"""Structured PCS rendering benchmark failure kinds (pcs-bench / repair routing)."""

from __future__ import annotations

from typing import Any

FAILURE_KINDS: tuple[str, ...] = (
    "import_failed",
    "render_failed",
    "query_failed",
    "staleness_failed",
    "comparison_failed",
    "formal_failed",
)

_DEFAULT_COMPONENT = "Scientific Memory"


def failure_event(
    kind: str,
    message: str,
    *,
    responsible_component: str = _DEFAULT_COMPONENT,
    repair_hint: str = "",
    artifact_path: str = "",
    what_was_still_imported: list[str] | None = None,
) -> dict[str, Any]:
    if kind not in FAILURE_KINDS:
        raise ValueError(f"unknown failure kind: {kind}")
    return {
        "kind": kind,
        "message": message,
        "responsible_component": responsible_component,
        "repair_hint": repair_hint,
        "artifact_path": artifact_path,
        "what_was_still_imported": list(what_was_still_imported or []),
    }


def summarize_failure_kinds(events: list[dict[str, Any]]) -> dict[str, bool]:
    kinds = {name: False for name in FAILURE_KINDS}
    for event in events:
        kind = str(event.get("kind") or "")
        if kind in kinds:
            kinds[kind] = True
    return kinds


def failure_messages(events: list[dict[str, Any]]) -> list[str]:
    return [f"{event['kind']}: {event['message']}" for event in events if event.get("message")]


def _failed_lean_rows(read_model: dict[str, Any]) -> list[dict[str, Any]]:
    kernel = read_model.get("formal_trust_kernel") or {}
    return [
        row
        for row in (kernel.get("lean_check_results") or [])
        if isinstance(row, dict) and str(row.get("result") or "").lower() == "failed"
    ]


def classify_section_failure_kind(missing_sections: list[str]) -> str:
    if missing_sections and all(section == "Formal Trust Kernel" for section in missing_sections):
        return "formal_failed"
    return "render_failed"


def classify_failure_evidence_kind(
    read_model: dict[str, Any],
    expected: dict[str, Any],
) -> str:
    """Route failure-mode benchmarks to formal_failed when Lean/formal evidence is the focus."""
    explicit = str(expected.get("failure_kind") or "").strip()
    if explicit in FAILURE_KINDS:
        return explicit
    if expected.get("formal_focus") or expected.get("require_formal_checks"):
        return "formal_failed"
    if _failed_lean_rows(read_model):
        return "formal_failed"
    return "render_failed"


def formal_failure_context(read_model: dict[str, Any]) -> tuple[str, str, list[str]]:
    """Responsible component, repair hint, and artifact paths from failed Lean rows."""
    rows = _failed_lean_rows(read_model)
    if not rows:
        return "Formal Trust Kernel", "Re-run Lean check and attach LeanCheckResult.v0 to the release.", []
    row = rows[0]
    component = str(row.get("responsible_component") or "Formal Trust Kernel")
    hint = str(row.get("repair_hint") or "Fix Lean proof or update proof_obligation.v0 / lean_check_result.v0.")
    artifacts = [str(a) for a in (row.get("source_artifacts") or []) if a]
    return component, hint, artifacts
