"""Query helpers for imported PCS claims."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def claims_root(repo_root: Path) -> Path:
    return repo_root / "corpus" / "pcs" / "claims"


def list_claim_ids(repo_root: Path) -> list[str]:
    root = claims_root(repo_root)
    if not root.is_dir():
        return []
    return sorted(
        path.name
        for path in root.iterdir()
        if path.is_dir() and (path / "read_model.json").is_file()
    )


def load_claim_bundle(repo_root: Path, claim_id: str) -> dict[str, Any]:
    path = claims_root(repo_root) / claim_id
    bundle_path = path / "signed_bundle.json"
    read_model_path = path / "read_model.json"
    if read_model_path.is_file():
        data = json.loads(read_model_path.read_text(encoding="utf-8-sig"))
        if isinstance(data, dict):
            return {
                "claim_id": claim_id,
                "claim_dir": str(path),
                "read_model": data,
                "lineage": _load_json(path / "lineage.json"),
                "import_report": _load_json(path / "scientific_memory_import_report.json"),
            }
    if bundle_path.is_file():
        return {
            "claim_id": claim_id,
            "claim_dir": str(path),
            "signed_bundle": _load_json(bundle_path),
            "lineage": _load_json(path / "lineage.json"),
            "import_report": _load_json(path / "scientific_memory_import_report.json"),
        }
    raise FileNotFoundError(f"claim not found: {claim_id}")


def _load_json(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    return data if isinstance(data, dict) else None


def list_claims_by_certificate(repo_root: Path, certificate_id: str) -> list[str]:
    from sm_pipeline.pcs_import.claim_index import query_claims_index

    return [
        str(entry["claim_id"])
        for entry in query_claims_index(repo_root, certificate_id=certificate_id)
        if entry.get("claim_id")
    ]


def list_claims_by_source_commit(repo_root: Path, commit: str) -> list[str]:
    from sm_pipeline.pcs_import.claim_index import query_claims_index

    return [
        str(entry["claim_id"])
        for entry in query_claims_index(repo_root, source_commit=commit)
        if entry.get("claim_id")
    ]


def list_claims_by_release_id(repo_root: Path, release_id: str) -> list[str]:
    from sm_pipeline.pcs_import.claim_index import query_claims_index

    return [
        str(entry["claim_id"])
        for entry in query_claims_index(repo_root, release_id=release_id)
        if entry.get("claim_id")
    ]


def list_claims_by_trace_hash(repo_root: Path, trace_hash: str) -> list[str]:
    from sm_pipeline.pcs_import.claim_index import query_claims_index

    return [
        str(entry["claim_id"])
        for entry in query_claims_index(repo_root, trace_hash=trace_hash)
        if entry.get("claim_id")
    ]


def list_stale_claims(repo_root: Path) -> list[str]:
    from sm_pipeline.pcs_import.claim_index import query_claims_index

    return [
        str(entry["claim_id"])
        for entry in query_claims_index(repo_root, stale_only=True)
        if entry.get("claim_id")
    ]


def refresh_all_stale_flags(repo_root: Path) -> list[dict[str, Any]]:
    """Recompute stale flags for every imported claim and rebuild the corpus index."""
    from sm_pipeline.pcs_import.claim_lineage import update_lineage_stale_flags
    from sm_pipeline.pcs_import.claim_index import write_claims_index

    results: list[dict[str, Any]] = []
    for claim_id in list_claim_ids(repo_root):
        claim_dir = claims_root(repo_root) / claim_id
        bundle_path = claim_dir / "signed_bundle.json"
        if not bundle_path.is_file():
            continue
        lineage = update_lineage_stale_flags(claim_dir, bundle_path=bundle_path)
        read_model_path = claim_dir / "read_model.json"
        if read_model_path.is_file():
            read_model = _load_json(read_model_path)
            if read_model is not None:
                read_model["staleness"] = {
                    "stale": bool(lineage.get("stale")),
                    "stale_reasons": list(lineage.get("stale_reasons") or []),
                }
                read_model_path.write_text(
                    json.dumps(read_model, indent=2, sort_keys=True) + "\n",
                    encoding="utf-8",
                )
        results.append({"claim_id": claim_id, "lineage": lineage})
    write_claims_index(repo_root)
    return results
