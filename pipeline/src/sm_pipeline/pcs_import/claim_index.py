"""Corpus-wide PCS claim index for cross-claim lineage queries."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from sm_pipeline.pcs_import.claim_query import claims_root, list_claim_ids

INDEX_FILENAME = "claims_index.json"
INDEX_SCHEMA_VERSION = "PcsClaimsIndex.v0"


def _load_json(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    return data if isinstance(data, dict) else None


def build_claim_index_entry(claim_dir: Path) -> dict[str, Any] | None:
    read_model = _load_json(claim_dir / "read_model.json")
    lineage = _load_json(claim_dir / "lineage.json")
    report = _load_json(claim_dir / "scientific_memory_import_report.json")
    if read_model is None and lineage is None:
        return None

    claim_id = str(
        (read_model or {}).get("claim_id")
        or (lineage or {}).get("claim_id")
        or claim_dir.name,
    )
    staleness = (read_model or {}).get("staleness")
    if not isinstance(staleness, dict) and isinstance(lineage, dict):
        staleness = {
            "stale": lineage.get("stale", False),
            "stale_reasons": lineage.get("stale_reasons") or [],
        }

    claim_state = "current"
    if isinstance(staleness, dict):
        if staleness.get("stale"):
            claim_state = str(staleness.get("claim_state") or "stale")
        else:
            claim_state = str(staleness.get("claim_state") or "current")
    elif isinstance(lineage, dict) and lineage.get("stale"):
        claim_state = "stale"

    workflow_profile_id = (lineage or {}).get("workflow_profile_id")
    if not workflow_profile_id:
        workflow_profile = (read_model or {}).get("workflow_profile")
        if isinstance(workflow_profile, dict):
            workflow_profile_id = workflow_profile.get("workflow_id")

    computation = (lineage or {}).get("computation")
    if not isinstance(computation, dict):
        computation = {}

    entry: dict[str, Any] = {
        "claim_id": claim_id,
        "claim_dir": claim_dir.name,
        "claim_state": claim_state,
        "release_id": (lineage or {}).get("release_id") or (report or {}).get("release_id"),
        "workflow_profile_id": workflow_profile_id,
        "release_candidate": (report or {}).get("release_candidate"),
        "certificate_id": (lineage or {}).get("certificate_id"),
        "trace_hash": (lineage or {}).get("trace_hash"),
        "dataset_id": computation.get("dataset_id"),
        "dataset_version": computation.get("dataset_version"),
        "environment_id": computation.get("environment_id"),
        "code_commit": computation.get("code_commit"),
        "result_hash": computation.get("result_hash"),
        "witness_id": computation.get("witness_id"),
        "witness_status": computation.get("witness_status"),
        "bundle_id": (lineage or {}).get("bundle_id"),
        "signed_bundle_hash": (lineage or {}).get("signed_bundle_hash")
        or (read_model or {}).get("signed_bundle_hash"),
        "release_manifest_hash": (lineage or {}).get("release_manifest_hash")
        or (read_model or {}).get("release_manifest_hash"),
        "source_commits": (lineage or {}).get("source_commits") or {},
        "stale": bool((staleness or {}).get("stale")),
        "stale_reasons": list((staleness or {}).get("stale_reasons") or []),
        "imported_at": (report or {}).get("imported_at"),
        "verification_status": (report or {}).get("verification_status"),
        "render_path": (report or {}).get("render_path") or f"/pcs/claims/{claim_id}",
    }
    return entry


def build_claims_index(repo_root: Path) -> dict[str, Any]:
    entries: list[dict[str, Any]] = []
    for claim_id in list_claim_ids(repo_root):
        claim_dir = claims_root(repo_root) / claim_id
        entry = build_claim_index_entry(claim_dir)
        if entry is not None:
            entries.append(entry)
    return {
        "schema_version": INDEX_SCHEMA_VERSION,
        "claim_count": len(entries),
        "claims": entries,
    }


def write_claims_index(repo_root: Path) -> Path:
    root = repo_root.resolve()
    pcs_dir = root / "corpus" / "pcs"
    pcs_dir.mkdir(parents=True, exist_ok=True)
    out = pcs_dir / INDEX_FILENAME
    index = build_claims_index(root)
    out.write_text(json.dumps(index, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return out


def load_claims_index(repo_root: Path) -> dict[str, Any]:
    path = repo_root.resolve() / "corpus" / "pcs" / INDEX_FILENAME
    if not path.is_file():
        return build_claims_index(repo_root)
    data = _load_json(path)
    if data is None or not isinstance(data.get("claims"), list):
        return build_claims_index(repo_root)
    return data


def query_claims_index(
    repo_root: Path,
    *,
    release_id: str | None = None,
    certificate_id: str | None = None,
    trace_hash: str | None = None,
    source_commit: str | None = None,
    release_manifest_hash: str | None = None,
    stale_only: bool = False,
    claim_state: str | None = None,
    workflow_profile_id: str | None = None,
    dataset_id: str | None = None,
    environment_id: str | None = None,
    code_commit: str | None = None,
    result_hash: str | None = None,
) -> list[dict[str, Any]]:
    index = load_claims_index(repo_root)
    claims = index.get("claims")
    if not isinstance(claims, list):
        return []

    matches: list[dict[str, Any]] = []
    for entry in claims:
        if not isinstance(entry, dict):
            continue
        if stale_only and not entry.get("stale"):
            continue
        if claim_state is not None and entry.get("claim_state") != claim_state:
            continue
        if release_id is not None and entry.get("release_id") != release_id:
            continue
        if workflow_profile_id is not None and entry.get("workflow_profile_id") != workflow_profile_id:
            continue
        if certificate_id is not None and entry.get("certificate_id") != certificate_id:
            continue
        if trace_hash is not None and entry.get("trace_hash") != trace_hash:
            continue
        if release_manifest_hash is not None and entry.get("release_manifest_hash") != release_manifest_hash:
            continue
        if source_commit is not None:
            commits = entry.get("source_commits")
            indexed_commit = entry.get("code_commit")
            if indexed_commit == source_commit:
                pass
            elif not isinstance(commits, dict) or source_commit not in commits.values():
                continue
        if dataset_id is not None and entry.get("dataset_id") != dataset_id:
            continue
        if environment_id is not None and entry.get("environment_id") != environment_id:
            continue
        if code_commit is not None and entry.get("code_commit") != code_commit:
            continue
        if result_hash is not None and entry.get("result_hash") != result_hash:
            continue
        matches.append(entry)
    return matches
