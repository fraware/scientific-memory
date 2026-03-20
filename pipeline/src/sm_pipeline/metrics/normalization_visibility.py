"""8.3 Normalization visibility: role_unclear symbols, claims without linked_assumptions."""

import json
from pathlib import Path


def compute_normalization_visibility(repo_root: Path) -> dict:
    """
    Report symbols with role_unclear and claims with empty linked_assumptions
    (where paper has assumptions). Supports triage; no auto-resolution.
    """
    repo_root = repo_root.resolve()
    papers_dir = repo_root / "corpus" / "papers"
    index_path = repo_root / "corpus" / "index.json"
    if not papers_dir.is_dir() or not index_path.exists():
        return _empty_result()

    index = json.loads(index_path.read_text(encoding="utf-8"))
    papers = index.get("papers") or []
    paper_ids = [p["id"] for p in papers if isinstance(p, dict) and p.get("id")]

    symbols_role_unclear: list[dict] = []
    claims_without_assumptions: list[dict] = []

    for paper_id in paper_ids:
        paper_dir = papers_dir / paper_id
        symbols_path = paper_dir / "symbols.json"
        claims_path = paper_dir / "claims.json"
        assumptions_path = paper_dir / "assumptions.json"

        if symbols_path.exists():
            try:
                data = json.loads(symbols_path.read_text(encoding="utf-8"))
                if isinstance(data, list):
                    for s in data:
                        if isinstance(s, dict):
                            flags = s.get("ambiguity_flags") or []
                            if "role_unclear" in flags:
                                symbols_role_unclear.append(
                                    {
                                        "paper_id": paper_id,
                                        "symbol_id": s.get("id", ""),
                                    }
                                )
            except (json.JSONDecodeError, OSError):
                pass

        has_assumptions = False
        if assumptions_path.exists():
            try:
                data = json.loads(assumptions_path.read_text(encoding="utf-8"))
                has_assumptions = isinstance(data, list) and len(data) > 0
            except (json.JSONDecodeError, OSError):
                pass

        if has_assumptions and claims_path.exists():
            try:
                data = json.loads(claims_path.read_text(encoding="utf-8"))
                if isinstance(data, list):
                    for c in data:
                        if not isinstance(c, dict):
                            continue
                        if c.get("linked_assumptions"):
                            continue
                        claims_without_assumptions.append(
                            {
                                "paper_id": paper_id,
                                "claim_id": c.get("id"),
                            }
                        )
            except (json.JSONDecodeError, OSError):
                pass

    return {
        "symbols_with_role_unclear": symbols_role_unclear,
        "symbols_with_role_unclear_count": len(symbols_role_unclear),
        "claims_without_linked_assumptions": claims_without_assumptions,
        "claims_without_linked_assumptions_count": len(claims_without_assumptions),
    }


def _empty_result() -> dict:
    return {
        "symbols_with_role_unclear": [],
        "symbols_with_role_unclear_count": 0,
        "claims_without_linked_assumptions": [],
        "claims_without_linked_assumptions_count": 0,
    }
