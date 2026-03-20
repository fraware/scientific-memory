"""Normalization utilities for symbols/assumptions/link resolution."""

from __future__ import annotations

import json
import re
from pathlib import Path


def normalize_paper(repo_root: Path, paper_id: str) -> dict:
    """
    Normalize paper extraction artifacts in-place.

    - canonicalize symbol normalized_name values
    - add `overloaded_symbol` ambiguity flag for duplicated normalized_name
    - populate minimal dimensional metadata when absent
    - default assumption normalization_status to "normalized"
    """
    repo_root = repo_root.resolve()
    paper_dir = repo_root / "corpus" / "papers" / paper_id
    if not paper_dir.is_dir():
        raise FileNotFoundError(f"Paper directory not found: {paper_dir}")

    symbols_path = paper_dir / "symbols.json"
    assumptions_path = paper_dir / "assumptions.json"
    claims_path = paper_dir / "claims.json"

    symbols = _read_json_array(symbols_path)
    assumptions = _read_json_array(assumptions_path)
    claims = _read_json_array(claims_path)

    symbol_name_to_ids: dict[str, list[str]] = {}
    symbol_id_map: dict[str, str] = {}
    for sym in symbols:
        sid = str(sym.get("id") or "")
        if not sid:
            continue
        normalized = _canonical_name(str(sym.get("normalized_name") or sym.get("raw_latex") or sid))
        sym["normalized_name"] = normalized
        symbol_id_map[sid] = sid
        symbol_name_to_ids.setdefault(normalized, []).append(sid)
        _ensure_dimensional_metadata(sym)
        flags = list(sym.get("ambiguity_flags") or [])
        if symbol_name_to_ids[normalized].__len__() > 1 and "overloaded_symbol" not in flags:
            flags.append("overloaded_symbol")
        sym["ambiguity_flags"] = sorted(set(str(f) for f in flags if f))

    for assumption in assumptions:
        if not assumption.get("normalization_status"):
            assumption["normalization_status"] = "normalized"

    assumption_ids = {str(a.get("id")) for a in assumptions if a.get("id")}
    symbol_ids = {str(s.get("id")) for s in symbols if s.get("id")}
    unresolved_assumptions = 0
    unresolved_symbols = 0
    for claim in claims:
        linked_a = [x for x in (claim.get("linked_assumptions") or []) if str(x) in assumption_ids]
        linked_s = [x for x in (claim.get("linked_symbols") or []) if str(x) in symbol_ids]
        unresolved_assumptions += len((claim.get("linked_assumptions") or [])) - len(linked_a)
        unresolved_symbols += len((claim.get("linked_symbols") or [])) - len(linked_s)
        claim["linked_assumptions"] = linked_a
        claim["linked_symbols"] = linked_s

    symbols_path.write_text(json.dumps(symbols, indent=2), encoding="utf-8")
    assumptions_path.write_text(json.dumps(assumptions, indent=2), encoding="utf-8")
    claims_path.write_text(json.dumps(claims, indent=2), encoding="utf-8")

    duplicate_name_count = sum(1 for v in symbol_name_to_ids.values() if len(v) > 1)
    out = {
        "paper_id": paper_id,
        "symbol_count": len(symbols),
        "assumption_count": len(assumptions),
        "duplicate_normalized_name_count": duplicate_name_count,
        "unresolved_assumption_links_removed": unresolved_assumptions,
        "unresolved_symbol_links_removed": unresolved_symbols,
    }
    (paper_dir / "normalization_report.json").write_text(
        json.dumps(out, indent=2), encoding="utf-8"
    )
    return out


def _canonical_name(value: str) -> str:
    s = value.strip().lower()
    s = re.sub(r"[^a-z0-9]+", "_", s)
    s = re.sub(r"_+", "_", s).strip("_")
    return s or "symbol"


def _ensure_dimensional_metadata(symbol: dict) -> None:
    md = symbol.get("dimensional_metadata")
    if not isinstance(md, dict):
        md = {}
    md.setdefault("kind", "unknown")
    md.setdefault("unit", "")
    md.setdefault("dimension", "")
    symbol["dimensional_metadata"] = md


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
