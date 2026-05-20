"""Structured PCS rendering benchmark failure kinds (pcs-bench / repair routing)."""

from __future__ import annotations

from typing import Any

FAILURE_KINDS: tuple[str, ...] = (
    "import_failed",
    "render_failed",
    "query_failed",
    "staleness_failed",
    "comparison_failed",
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
