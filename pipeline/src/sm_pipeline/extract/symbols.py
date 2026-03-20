"""Symbol extraction helpers (deterministic heuristic baseline)."""

from __future__ import annotations

import json
import re
from pathlib import Path

_TOKEN_RE = re.compile(r"\b[a-zA-Z][a-zA-Z0-9_]*\b")
_STOPWORDS = {
    "the",
    "and",
    "for",
    "with",
    "from",
    "that",
    "this",
    "when",
    "then",
    "into",
    "over",
    "paper",
    "claim",
}


def extract_symbols(repo_root: Path, paper_id: str) -> list[dict]:
    """
    Derive symbols from claims text when symbols.json is missing or empty.

    This favors deterministic reproducibility over high recall and is designed
    as an initial extraction pass for human review.
    """
    repo_root = repo_root.resolve()
    paper_dir = repo_root / "corpus" / "papers" / paper_id
    if not paper_dir.is_dir():
        raise FileNotFoundError(f"Paper directory not found: {paper_dir}")

    symbols_path = paper_dir / "symbols.json"
    existing = _read_json_array(symbols_path)
    if existing:
        return existing

    claims = _read_json_array(paper_dir / "claims.json")
    seen: set[str] = set()
    symbols: list[dict] = []
    for claim in claims:
        text = str(claim.get("informal_text") or "")
        for token in _TOKEN_RE.findall(text):
            tok = token.lower()
            if tok in _STOPWORDS or len(tok) < 2:
                continue
            if tok in seen:
                continue
            seen.add(tok)
            symbol_id = f"{paper_id.replace('-', '_')}_sym_{tok}"
            symbols.append(
                {
                    "id": symbol_id,
                    "paper_id": paper_id,
                    "raw_latex": token,
                    "normalized_name": tok,
                    "type_hint": "Real",
                    "dimensional_metadata": {
                        "kind": "unknown",
                        "unit": "",
                        "dimension": "",
                    },
                    "ambiguity_flags": [],
                }
            )
            if len(symbols) >= 24:
                break
        if len(symbols) >= 24:
            break

    symbols_path.write_text(json.dumps(symbols, indent=2), encoding="utf-8")
    return symbols


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
