"""Flag PCS artifacts whose status is Stale or Deprecated."""

from __future__ import annotations

from typing import Any


STALE_STATUSES = frozenset({"Stale", "Deprecated"})


def find_stale_artifacts(bundle: dict[str, Any]) -> list[str]:
    """Return artifact paths (dot-separated) with Stale or Deprecated status."""
    stale: list[str] = []
    scb = bundle.get("science_claim_bundle")
    if not isinstance(scb, dict):
        return stale

    for key in (
        "claim",
        "assumption_set",
        "runtime_receipt",
        "trace_certificate",
        "evidence_bundle",
        "verification_result",
    ):
        artifact = scb.get(key)
        if isinstance(artifact, dict):
            _check_artifact(f"science_claim_bundle.{key}", artifact, stale)

    vr = bundle.get("verification_result")
    if isinstance(vr, dict):
        _check_artifact("verification_result", vr, stale)

    return stale


def _check_artifact(path: str, artifact: dict[str, Any], out: list[str]) -> None:
    status = str(artifact.get("status") or "")
    if status in STALE_STATUSES:
        out.append(path)
