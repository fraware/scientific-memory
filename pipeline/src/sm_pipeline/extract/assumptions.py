"""Assumption extraction helpers (deterministic, corpus-first)."""

from __future__ import annotations

import json
from pathlib import Path


def extract_assumptions(repo_root: Path, paper_id: str) -> list[dict]:
    """
    Materialize assumptions.json for a paper when missing/empty.

    This is intentionally conservative and deterministic: it creates one baseline
    domain restriction assumption linked to the paper's source span, so every
    claim bundle can attach explicit provenance-backed assumptions.
    """
    repo_root = repo_root.resolve()
    paper_dir = repo_root / "corpus" / "papers" / paper_id
    if not paper_dir.is_dir():
        raise FileNotFoundError(f"Paper directory not found: {paper_dir}")

    metadata_path = paper_dir / "metadata.json"
    if not metadata_path.exists():
        raise FileNotFoundError(f"Paper metadata not found: {metadata_path}")
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    source_file = str((metadata.get("source") or {}).get("path") or "source/source.pdf")

    assumptions_path = paper_dir / "assumptions.json"
    existing = _read_json_array(assumptions_path)
    if existing:
        return existing

    aid = f"{paper_id.replace('-', '_')}_assumption_001"
    assumptions = [
        {
            "id": aid,
            "paper_id": paper_id,
            "source_span": {
                "source_file": source_file,
                "start": {"page": 1, "offset": 0},
                "end": {"page": 1, "offset": 120},
            },
            "text": (
                "Quantities used by extracted claims are interpreted within the "
                "paper's empirical/scientific regime."
            ),
            "kind": "domain_restriction",
            "explicit_or_implicit": "implicit",
            "normalization_status": "raw",
        }
    ]
    assumptions_path.write_text(json.dumps(assumptions, indent=2), encoding="utf-8")
    return assumptions


def _read_json_array(path: Path) -> list[dict]:
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []
    if isinstance(data, list):
        return [x for x in data if isinstance(x, dict)]
    return []
