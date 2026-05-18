"""Operational lineage: cross-release comparison and staleness views."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from sm_pipeline.pcs_import.claim_index import load_claims_index
from sm_pipeline.pcs_import.claim_lineage import load_lineage
from sm_pipeline.pcs_import.stale_check import normalize_stale_reason
from sm_pipeline.pcs_import.claim_query import claims_root
from sm_pipeline.pcs_import.stale_check import STALE_REPAIR_HINT

CLAIM_STATES = frozenset({"current", "stale", "superseded", "withdrawn", "revalidated"})


def _load_json(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    import json

    data = json.loads(path.read_text(encoding="utf-8-sig"))
    return data if isinstance(data, dict) else None


def _related_index_entries(
    repo_root: Path,
    *,
    claim_id: str,
    certificate_id: str | None,
) -> list[dict[str, Any]]:
    index = load_claims_index(repo_root)
    claims = index.get("claims")
    if not isinstance(claims, list):
        return []
    related: list[dict[str, Any]] = []
    for entry in claims:
        if not isinstance(entry, dict):
            continue
        if certificate_id and entry.get("certificate_id") == certificate_id:
            related.append(entry)
        elif entry.get("claim_id") == claim_id:
            related.append(entry)
    return sorted(related, key=lambda row: str(row.get("imported_at") or ""))


def _lineage_artifact_hashes(claim_dir: Path) -> dict[str, str]:
    lineage = load_lineage(claim_dir)
    if lineage is None:
        return {}
    hashes = lineage.get("artifact_hashes")
    return dict(hashes) if isinstance(hashes, dict) else {}


def diff_artifact_hashes(
    current: dict[str, str],
    previous: dict[str, str],
) -> tuple[list[str], list[dict[str, str]]]:
    changed_names: list[str] = []
    changed_rows: list[dict[str, str]] = []
    names = sorted(set(current) | set(previous))
    for name in names:
        cur = current.get(name, "")
        prev = previous.get(name, "")
        if cur != prev:
            changed_names.append(name)
            changed_rows.append({"artifact": name, "previous": prev, "current": cur})
    return changed_names, changed_rows


def resolve_claim_state(
    lineage: dict[str, Any],
    *,
    release_manifest: dict[str, Any] | None = None,
    validation: dict[str, Any] | None = None,
    newer_release_ids: list[str] | None = None,
) -> str:
    release_status = str((release_manifest or {}).get("release_status") or "").lower()
    if release_status in ("withdrawn", "rejected"):
        return "withdrawn"

    validation_status = str((validation or {}).get("status") or "")
    if validation_status and validation_status != "ProofChecked":
        return "stale"

    if newer_release_ids:
        return "superseded"

    if lineage.get("stale"):
        return "stale"

    if lineage.get("revalidated"):
        return "revalidated"

    return "current"


def recommended_action_for_state(claim_state: str, *, stale: bool) -> str:
    if claim_state == "withdrawn":
        return "Do not use this release; import a current validated release instead."
    if claim_state == "superseded":
        return "Open the newer release for this certificate or re-import the latest ReleaseManifest.v0."
    if stale or claim_state == "stale":
        return STALE_REPAIR_HINT
    if claim_state == "revalidated":
        return "Claim was revalidated; confirm portal export matches the latest on-disk artifacts."
    return "No action required; claim matches imported release artifacts."


def build_operational_lineage_view(
    lineage: dict[str, Any],
    *,
    repo_root: Path,
    claim_id: str,
    release_manifest: dict[str, Any] | None = None,
    validation: dict[str, Any] | None = None,
) -> dict[str, Any]:
    root = repo_root.resolve()
    claim_dir = claims_root(root) / claim_id
    certificate_id = str(lineage.get("certificate_id") or "")
    related = _related_index_entries(root, claim_id=claim_id, certificate_id=certificate_id or None)

    previous_release_id = ""
    newer_release_ids: list[str] = []
    current_imported_at = ""
    for entry in related:
        if entry.get("claim_id") == claim_id:
            current_imported_at = str(entry.get("imported_at") or "")
            break

    for entry in related:
        rid = str(entry.get("release_id") or "")
        imported_at = str(entry.get("imported_at") or "")
        if entry.get("claim_id") == claim_id:
            continue
        if imported_at and current_imported_at and imported_at < current_imported_at:
            previous_release_id = rid or previous_release_id
        elif imported_at and current_imported_at and imported_at > current_imported_at:
            if rid:
                newer_release_ids.append(rid)

    changed_artifacts: list[str] = []
    changed_hashes: list[dict[str, str]] = []
    if previous_release_id:
        for entry in related:
            if entry.get("release_id") != previous_release_id:
                continue
            prev_dir = claims_root(root) / str(entry.get("claim_dir") or entry.get("claim_id") or "")
            changed_artifacts, changed_hashes = diff_artifact_hashes(
                _lineage_artifact_hashes(claim_dir),
                _lineage_artifact_hashes(prev_dir),
            )
            break

    claim_state = resolve_claim_state(
        lineage,
        release_manifest=release_manifest,
        validation=validation,
        newer_release_ids=newer_release_ids,
    )
    reasons = [
        normalize_stale_reason(str(reason))
        for reason in (lineage.get("stale_reasons") or [])
        if str(reason).strip()
    ]

    view = dict(lineage)
    view["claim_state"] = claim_state
    view["previous_release_id"] = previous_release_id or None
    view["newer_release_ids"] = newer_release_ids
    view["changed_artifacts"] = changed_artifacts
    view["changed_hashes"] = changed_hashes
    view["recommended_action"] = recommended_action_for_state(
        claim_state,
        stale=bool(lineage.get("stale")),
    )
    view["stale_reasons"] = reasons
    return view


def build_operational_staleness_view(
    lineage: dict[str, Any],
    *,
    repo_root: Path,
    claim_id: str,
    release_manifest: dict[str, Any] | None = None,
    validation: dict[str, Any] | None = None,
) -> dict[str, Any]:
    operational = build_operational_lineage_view(
        lineage,
        repo_root=repo_root,
        claim_id=claim_id,
        release_manifest=release_manifest,
        validation=validation,
    )
    stale = bool(operational.get("stale"))
    claim_state = str(operational.get("claim_state") or ("stale" if stale else "current"))
    reasons = list(operational.get("stale_reasons") or [])
    return {
        "stale": stale,
        "stale_reasons": reasons,
        "claim_state": claim_state,
        "repair_hint": STALE_REPAIR_HINT if stale else "",
        "recommended_action": operational.get("recommended_action", ""),
    }
