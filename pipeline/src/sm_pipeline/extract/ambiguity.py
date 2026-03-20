"""Suggest or populate ambiguity_flags on symbols (SPEC 8.2). Heuristics: duplicate normalized_name -> overloaded_symbol; dimension without unit -> unit_unclear."""

import json
from pathlib import Path


VALID_FLAGS = frozenset({"overloaded_symbol", "unit_unclear", "scope_unclear", "role_unclear"})


def suggest_ambiguity_flags(paper_dir: Path) -> list[dict]:
    """
    Read symbols.json; return (symbol_index, suggested_flags) for symbols
    that might need ambiguity_flags. Does not mutate files.
    """
    symbols_path = paper_dir / "symbols.json"
    if not symbols_path.exists():
        return []
    try:
        symbols = json.loads(symbols_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []
    if not isinstance(symbols, list):
        return []

    normalized_counts: dict[str, int] = {}
    for s in symbols:
        if isinstance(s, dict) and s.get("normalized_name"):
            n = str(s["normalized_name"])
            normalized_counts[n] = normalized_counts.get(n, 0) + 1

    suggestions: list[dict] = []
    for i, s in enumerate(symbols):
        if not isinstance(s, dict):
            continue
        suggested: list[str] = list(s.get("ambiguity_flags") or [])
        if not isinstance(suggested, list):
            suggested = []

        name = str(s.get("normalized_name", ""))
        if name and normalized_counts.get(name, 0) > 1 and "overloaded_symbol" not in suggested:
            suggested.append("overloaded_symbol")

        dim_meta = s.get("dimensional_metadata")
        if isinstance(dim_meta, dict) and dim_meta.get("dimension") and not dim_meta.get("unit"):
            if "unit_unclear" not in suggested:
                suggested.append("unit_unclear")

        suggested = [f for f in suggested if f in VALID_FLAGS]
        if suggested:
            suggestions.append({"index": i, "id": s.get("id"), "suggested_flags": suggested})
    return suggestions


def apply_ambiguity_suggestions(paper_dir: Path, write_back: bool = True) -> list[dict]:
    """
    Merge suggested flags into ambiguity_flags (union with existing) per symbol.
    If write_back, write updated symbols.json. Returns list of applied suggestions.
    """
    symbols_path = paper_dir / "symbols.json"
    if not symbols_path.exists():
        return []
    try:
        symbols = json.loads(symbols_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []
    if not isinstance(symbols, list):
        return []

    normalized_counts: dict[str, int] = {}
    for s in symbols:
        if isinstance(s, dict) and s.get("normalized_name"):
            n = str(s["normalized_name"])
            normalized_counts[n] = normalized_counts.get(n, 0) + 1

    applied: list[dict] = []
    for i, s in enumerate(symbols):
        if not isinstance(s, dict):
            continue
        existing = list(s.get("ambiguity_flags") or [])
        if not isinstance(existing, list):
            existing = []
        existing_set = set(f for f in existing if f in VALID_FLAGS)

        name = str(s.get("normalized_name", ""))
        if name and normalized_counts.get(name, 0) > 1:
            existing_set.add("overloaded_symbol")
        dim_meta = s.get("dimensional_metadata")
        if isinstance(dim_meta, dict) and dim_meta.get("dimension") and not dim_meta.get("unit"):
            existing_set.add("unit_unclear")

        new_flags = sorted(existing_set)
        if new_flags != sorted(set(existing)):
            s["ambiguity_flags"] = new_flags
            applied.append({"index": i, "id": s.get("id"), "ambiguity_flags": new_flags})

    if write_back and applied:
        symbols_path.write_text(json.dumps(symbols, indent=2), encoding="utf-8")
    return applied
