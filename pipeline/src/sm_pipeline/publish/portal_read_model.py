"""Canonical portal read model: build bundle dict for export (SPEC: schema-first portal data)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

# Single source for the portal export schema version string (keep in sync with portal consumers).
PORTAL_BUNDLE_VERSION = "0.1"


def load_paper_bundle(repo_root: Path, paper_id: str) -> dict[str, Any]:
    """Load all JSON artifacts for one paper into a single dict."""
    repo_root = repo_root.resolve()
    paper_dir = repo_root / "corpus" / "papers" / paper_id
    return {
        "metadata": _read_json_object(paper_dir / "metadata.json"),
        "claims": _read_json_array(paper_dir / "claims.json"),
        "assumptions": _read_json_array(paper_dir / "assumptions.json"),
        "symbols": _read_json_array(paper_dir / "symbols.json"),
        "mapping": _read_json_object(paper_dir / "mapping.json"),
        "manifest": _read_json_object(paper_dir / "manifest.json"),
        "theorem_cards": _read_json_array(paper_dir / "theorem_cards.json"),
    }


def build_portal_bundle(repo_root: Path) -> dict[str, Any]:
    """
    Build the full portal export structure (version, papers_index, papers map, kernels).
    This is the single projection used by export_portal_data.
    """
    repo_root = repo_root.resolve()
    papers_index = _read_json_object(repo_root / "corpus" / "index.json")
    papers = papers_index.get("papers") or []
    paper_map: dict[str, dict[str, Any]] = {}
    if isinstance(papers, list):
        for p in papers:
            if not isinstance(p, dict):
                continue
            paper_id = str(p.get("id") or "").strip()
            if not paper_id:
                continue
            paper_map[paper_id] = load_paper_bundle(repo_root, paper_id)
    return {
        "version": PORTAL_BUNDLE_VERSION,
        "papers_index": papers_index,
        "papers": paper_map,
        "kernels": _read_json_array(repo_root / "corpus" / "kernels.json"),
    }


def _read_json_array(path: Path) -> list:
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []
    return data if isinstance(data, list) else []


def _read_json_object(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}
    return data if isinstance(data, dict) else {}
