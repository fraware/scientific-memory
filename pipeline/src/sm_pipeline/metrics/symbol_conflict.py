"""Symbol normalization conflict rate: ambiguity_flags and overloaded normalized_name (SPEC 12)."""

import json
from pathlib import Path


def compute_symbol_conflict_rates(repo_root: Path) -> dict:
    """
    Per paper and aggregate: count symbols with non-empty ambiguity_flags;
    count symbols that share the same normalized_name within a paper (overloaded).
    Informational only; no validation change.
    """
    repo_root = repo_root.resolve()
    papers_dir = repo_root / "corpus" / "papers"
    index_path = repo_root / "corpus" / "index.json"
    if not papers_dir.is_dir() or not index_path.exists():
        return {"papers": {}, "aggregate": _empty_aggregate()}
    index = json.loads(index_path.read_text(encoding="utf-8"))
    paper_list = index.get("papers") or []
    paper_ids = [p["id"] for p in paper_list if isinstance(p, dict) and p.get("id")]

    total_with_flags = 0
    total_overloaded = 0
    total_symbols = 0
    by_paper: dict[str, dict] = {}

    for paper_id in paper_ids:
        symbols_path = papers_dir / paper_id / "symbols.json"
        if not symbols_path.exists():
            continue
        try:
            symbols = json.loads(symbols_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        if not isinstance(symbols, list):
            continue

        with_flags = sum(
            1 for s in symbols if isinstance(s, dict) and (s.get("ambiguity_flags") or [])
        )
        name_counts: dict[str, int] = {}
        for s in symbols:
            if isinstance(s, dict) and s.get("normalized_name"):
                n = str(s["normalized_name"])
                name_counts[n] = name_counts.get(n, 0) + 1
        symbols_in_overloaded_group = sum(c for c in name_counts.values() if c > 1)
        total_symbols += len(symbols)
        total_with_flags += with_flags
        total_overloaded += symbols_in_overloaded_group
        by_paper[paper_id] = {
            "symbol_count": len(symbols),
            "with_ambiguity_flags": with_flags,
            "symbols_with_overloaded_name": symbols_in_overloaded_group,
        }

    conflict_symbols = total_with_flags + total_overloaded
    aggregate = {
        "total_symbols": total_symbols,
        "total_with_ambiguity_flags": total_with_flags,
        "total_symbols_overloaded_name": total_overloaded,
        "symbol_conflict_rate": (conflict_symbols / total_symbols if total_symbols else 0.0),
    }
    return {"papers": by_paper, "aggregate": aggregate}


def compute_cross_paper_normalized_duplicates(repo_root: Path) -> dict:
    """
    Report symbols that share the same normalized_name across different papers
    (8.3 normalization visibility; report only, no validation).
    """
    repo_root = repo_root.resolve()
    papers_dir = repo_root / "corpus" / "papers"
    index_path = repo_root / "corpus" / "index.json"
    if not papers_dir.is_dir() or not index_path.exists():
        return {"by_name": {}, "duplicate_names": [], "count": 0, "suggest_merge": []}
    index = json.loads(index_path.read_text(encoding="utf-8"))
    paper_list = index.get("papers") or []
    paper_ids = [p["id"] for p in paper_list if isinstance(p, dict) and p.get("id")]

    name_to_locations: dict[str, list[dict]] = {}
    for paper_id in paper_ids:
        symbols_path = papers_dir / paper_id / "symbols.json"
        if not symbols_path.exists():
            continue
        try:
            symbols = json.loads(symbols_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        if not isinstance(symbols, list):
            continue
        for i, s in enumerate(symbols):
            if not isinstance(s, dict) or not s.get("normalized_name"):
                continue
            name = str(s["normalized_name"])
            loc = {"paper_id": paper_id, "symbol_id": s.get("id") or f"index_{i}"}
            name_to_locations.setdefault(name, []).append(loc)

    duplicate_names = [
        name
        for name, locs in name_to_locations.items()
        if len(set(loc["paper_id"] for loc in locs)) > 1
    ]
    by_name = {
        name: locs
        for name, locs in name_to_locations.items()
        if len(locs) > 1 and len(set(loc["paper_id"] for loc in locs)) > 1
    }
    suggest_merge = [
        {
            "normalized_name": name,
            "locations": locs,
            "note": "Same normalized_name across papers; consider canonical merge or document.",
        }
        for name, locs in by_name.items()
    ]
    return {
        "by_name": by_name,
        "duplicate_names": sorted(duplicate_names),
        "count": len(duplicate_names),
        "suggest_merge": suggest_merge,
    }


def _empty_aggregate() -> dict:
    return {
        "total_symbols": 0,
        "total_with_ambiguity_flags": 0,
        "total_symbols_overloaded_name": 0,
        "symbol_conflict_rate": 0.0,
    }
