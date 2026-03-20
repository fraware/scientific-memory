"""8.3 Assumption-lifting suggestions: suggest candidates for claims with none."""

import json
import re
from pathlib import Path


def _tokenize(text: str) -> set[str]:
    """Lowercase alphanumeric tokens for overlap scoring."""
    if not text or not isinstance(text, str):
        return set()
    return set(re.findall(r"[a-z0-9]+", text.lower()))


def _overlap_score(claim_tokens: set[str], assumption_tokens: set[str]) -> float:
    """Jaccard-like score: |intersection|/|union|. 0 if either empty."""
    if not claim_tokens or not assumption_tokens:
        return 0.0
    inter = len(claim_tokens & assumption_tokens)
    union = len(claim_tokens | assumption_tokens)
    return inter / union if union else 0.0


def compute_assumption_suggestions(repo_root: Path) -> dict:
    """
    For claims with empty linked_assumptions (in papers that have assumptions),
    suggest candidate assumption IDs from the same paper by text overlap.
    Output is for human triage; no auto-edit of corpus.
    """
    repo_root = repo_root.resolve()
    papers_dir = repo_root / "corpus" / "papers"
    index_path = repo_root / "corpus" / "index.json"
    if not papers_dir.is_dir() or not index_path.exists():
        return _empty_result()

    index = json.loads(index_path.read_text(encoding="utf-8"))
    papers = index.get("papers") or []
    paper_ids = [p["id"] for p in papers if isinstance(p, dict) and p.get("id")]

    suggestions: list[dict] = []

    for paper_id in paper_ids:
        paper_dir = papers_dir / paper_id
        claims_path = paper_dir / "claims.json"
        assumptions_path = paper_dir / "assumptions.json"
        if not claims_path.exists() or not assumptions_path.exists():
            continue
        try:
            claims = json.loads(claims_path.read_text(encoding="utf-8"))
            assumptions = json.loads(assumptions_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        if not isinstance(claims, list) or not isinstance(assumptions, list):
            continue
        if not assumptions:
            continue

        # assumption id -> tokens
        assumption_tokens: dict[str, set[str]] = {}
        for a in assumptions:
            if not isinstance(a, dict):
                continue
            aid = a.get("id")
            text = a.get("text") or ""
            if aid:
                assumption_tokens[aid] = _tokenize(text)

        for c in claims:
            if not isinstance(c, dict):
                continue
            if c.get("linked_assumptions"):
                continue
            claim_id = c.get("id")
            informal = c.get("informal_text") or ""
            section = c.get("section") or ""
            claim_tokens = _tokenize(informal + " " + section)
            if not claim_tokens:
                continue

            scored: list[tuple[str, float]] = []
            for aid, atok in assumption_tokens.items():
                score = _overlap_score(claim_tokens, atok)
                if score > 0:
                    scored.append((aid, score))
            scored.sort(key=lambda x: -x[1])

            if scored:
                suggestions.append(
                    {
                        "paper_id": paper_id,
                        "claim_id": claim_id,
                        "candidates": [
                            {"assumption_id": aid, "score": round(s, 4)} for aid, s in scored[:5]
                        ],
                    }
                )

    return {
        "assumption_suggestions": suggestions,
        "suggestion_count": len(suggestions),
    }


def _empty_result() -> dict:
    return {
        "assumption_suggestions": [],
        "suggestion_count": 0,
    }
