"""Structured stale-check payloads for CLI and automation."""

from __future__ import annotations

from typing import Any

STALE_REPAIR_HINT = (
    "Re-import the current release manifest or compare lineage against the latest canonical release."
)


def normalize_stale_reason(reason: str) -> str:
    return reason.strip().lower().replace(" ", "_")


def build_stale_check_result(claim_id: str, lineage: dict[str, Any]) -> dict[str, Any]:
    stale = bool(lineage.get("stale"))
    reasons = [
        normalize_stale_reason(str(reason))
        for reason in (lineage.get("stale_reasons") or [])
        if str(reason).strip()
    ]
    claim_state = str(lineage.get("claim_state") or ("stale" if stale else "current"))
    return {
        "claim_id": claim_id,
        "stale": stale,
        "stale_reasons": reasons,
        "claim_state": claim_state,
        "repair_hint": STALE_REPAIR_HINT if stale else "",
        "recommended_action": str(lineage.get("recommended_action") or ""),
    }
