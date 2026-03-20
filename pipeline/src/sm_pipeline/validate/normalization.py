"""Normalization validation (SPEC 8.3): unique IDs and resolved edges."""

import json
from pathlib import Path


class NormalizationError(Exception):
    """Raised when duplicate IDs or unresolved edges are found."""

    pass


def validate_normalization(repo_root: Path) -> None:
    """
    Per paper: ensure claim, assumption, and symbol IDs are unique;
    ensure claim linked_assumptions and linked_symbols resolve to existing IDs.
    """
    repo_root = repo_root.resolve()
    papers_dir = repo_root / "corpus" / "papers"
    if not papers_dir.is_dir():
        return

    for paper_dir in sorted(papers_dir.iterdir()):
        if not paper_dir.is_dir():
            continue
        paper_id = paper_dir.name

        claims_path = paper_dir / "claims.json"
        if not claims_path.exists():
            continue
        try:
            claims = json.loads(claims_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        if not isinstance(claims, list):
            continue

        assumption_id_list: list[str] = []
        assumptions_path = paper_dir / "assumptions.json"
        if assumptions_path.exists():
            try:
                assumptions = json.loads(assumptions_path.read_text(encoding="utf-8"))
                if isinstance(assumptions, list):
                    for a in assumptions:
                        if isinstance(a, dict) and a.get("id") is not None:
                            assumption_id_list.append(str(a["id"]))
            except (json.JSONDecodeError, OSError):
                pass
        assumption_ids = set(assumption_id_list)

        symbol_id_list: list[str] = []
        symbols_path = paper_dir / "symbols.json"
        if symbols_path.exists():
            try:
                symbols = json.loads(symbols_path.read_text(encoding="utf-8"))
                if isinstance(symbols, list):
                    for s in symbols:
                        if isinstance(s, dict) and s.get("id") is not None:
                            symbol_id_list.append(str(s["id"]))
            except (json.JSONDecodeError, OSError):
                pass
        symbol_ids = set(symbol_id_list)

        claim_ids = []
        for c in claims:
            if isinstance(c, dict) and c.get("id") is not None:
                claim_ids.append(str(c["id"]))

        dup_claims = _duplicates(claim_ids)
        dup_assumptions = _duplicates(assumption_id_list)
        dup_symbols = _duplicates(symbol_id_list)
        if dup_claims or dup_assumptions or dup_symbols:
            parts = []
            if dup_claims:
                parts.append(f"paper {paper_id} duplicate claim IDs: {sorted(dup_claims)}")
            if dup_assumptions:
                parts.append(
                    f"paper {paper_id} duplicate assumption IDs: {sorted(dup_assumptions)}"
                )
            if dup_symbols:
                parts.append(f"paper {paper_id} duplicate symbol IDs: {sorted(dup_symbols)}")
            raise NormalizationError("; ".join(parts))

        for c in claims:
            if not isinstance(c, dict):
                continue
            linked_assumptions = c.get("linked_assumptions")
            if isinstance(linked_assumptions, list):
                for aid in linked_assumptions:
                    if aid is not None and str(aid) not in assumption_ids:
                        raise NormalizationError(
                            f"paper {paper_id} claim {c.get('id')} linked_assumptions references missing ID: {aid}"
                        )
            linked_symbols = c.get("linked_symbols")
            if isinstance(linked_symbols, list):
                for sid in linked_symbols:
                    if sid is not None and str(sid) not in symbol_ids:
                        raise NormalizationError(
                            f"paper {paper_id} claim {c.get('id')} linked_symbols references missing ID: {sid}"
                        )


def _duplicates(ids: list[str]) -> set[str]:
    """Return set of IDs that appear more than once."""
    seen: set[str] = set()
    dups: set[str] = set()
    for i in ids:
        if i in seen:
            dups.add(i)
        seen.add(i)
    return dups
