"""Scaffold benchmarks/gold/<paper_id>/ from corpus claims and assumptions.

Run after adding a paper or when creating gold for a new paper. Creates gold
directory with claims.json (copy of corpus), source_spans.json (from claim
source_span), and assumptions.json (copy of corpus). Curation can follow.
"""

import json
from pathlib import Path


def scaffold_gold(repo_root: Path, paper_id: str) -> dict:
    """
    Create benchmarks/gold/<paper_id>/ from corpus papers/<paper_id>/.

    - claims.json: copy of corpus claims.json (same schema; match by id).
    - source_spans.json: list of { "claim_id", "source_span" } for claims
      that have source_span.
    - assumptions.json: copy of corpus assumptions.json if present.

    Returns summary: gold_dir, claims_count, source_spans_count, assumptions_count.
    """
    repo_root = repo_root.resolve()
    paper_dir = repo_root / "corpus" / "papers" / paper_id
    gold_dir = repo_root / "benchmarks" / "gold" / paper_id

    if not paper_dir.is_dir():
        raise FileNotFoundError(f"Paper directory not found: {paper_dir}")

    gold_dir.mkdir(parents=True, exist_ok=True)

    claims_path = paper_dir / "claims.json"
    claims: list = []
    if claims_path.exists():
        try:
            data = json.loads(claims_path.read_text(encoding="utf-8"))
            claims = data if isinstance(data, list) else []
        except (json.JSONDecodeError, OSError):
            pass

    source_spans: list = []
    for c in claims:
        if not isinstance(c, dict):
            continue
        cid = c.get("id")
        raw = c.get("source_span")
        span = raw if isinstance(raw, dict) else None
        if cid and span:
            source_spans.append({"claim_id": cid, "source_span": span})

    assumptions: list = []
    assumptions_path = paper_dir / "assumptions.json"
    if assumptions_path.exists():
        try:
            data = json.loads(assumptions_path.read_text(encoding="utf-8"))
            assumptions = data if isinstance(data, list) else []
        except (json.JSONDecodeError, OSError):
            pass

    (gold_dir / "claims.json").write_text(json.dumps(claims, indent=2), encoding="utf-8")
    if source_spans:
        (gold_dir / "source_spans.json").write_text(
            json.dumps(source_spans, indent=2), encoding="utf-8"
        )
    if assumptions:
        (gold_dir / "assumptions.json").write_text(
            json.dumps(assumptions, indent=2), encoding="utf-8"
        )

    return {
        "gold_dir": str(gold_dir),
        "claims_count": len(claims),
        "source_spans_count": len(source_spans),
        "assumptions_count": len(assumptions),
    }
