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
    matches: list[str] = []
    for claim_id in list_claim_ids(repo_root):
        lineage = _load_json(claims_root(repo_root) / claim_id / "lineage.json")
        if isinstance(lineage, dict) and lineage.get("certificate_id") == certificate_id:
            matches.append(claim_id)
    return matches


def list_claims_by_source_commit(repo_root: Path, commit: str) -> list[str]:
    matches: list[str] = []
    for claim_id in list_claim_ids(repo_root):
        lineage = _load_json(claims_root(repo_root) / claim_id / "lineage.json")
        if not isinstance(lineage, dict):
            continue
        commits = lineage.get("source_commits")
        if isinstance(commits, dict) and commit in commits.values():
            matches.append(claim_id)
    return matches
