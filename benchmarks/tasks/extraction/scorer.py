"""Extraction benchmark: claim/source-span and assumption metrics."""

import json
from pathlib import Path


def run(repo_root: Path) -> dict:
    """Compute extraction metrics over corpus. Returns a dict for the report."""
    papers_dir = repo_root / "corpus" / "papers"
    if not papers_dir.is_dir():
        return {
            "paper_count": 0,
            "claim_count": 0,
            "claims_with_source_span": 0,
            "assumption_count": 0,
        }

    paper_count = 0
    claim_count = 0
    claims_with_source_span = 0
    assumption_count = 0

    for paper_dir in sorted(papers_dir.iterdir()):
        if not paper_dir.is_dir():
            continue
        metadata_path = paper_dir / "metadata.json"
        if not metadata_path.exists():
            continue
        paper_count += 1

        claims_path = paper_dir / "claims.json"
        if claims_path.exists():
            try:
                claims = json.loads(claims_path.read_text(encoding="utf-8"))
                if isinstance(claims, list):
                    claim_count += len(claims)
                    for c in claims:
                        if isinstance(c, dict) and c.get("source_span"):
                            claims_with_source_span += 1
            except (json.JSONDecodeError, OSError):
                pass

        assumptions_path = paper_dir / "assumptions.json"
        if assumptions_path.exists():
            try:
                assumptions = json.loads(assumptions_path.read_text(encoding="utf-8"))
                if isinstance(assumptions, list):
                    assumption_count += len(assumptions)
            except (json.JSONDecodeError, OSError):
                pass

    return {
        "paper_count": paper_count,
        "claim_count": claim_count,
        "claims_with_source_span": claims_with_source_span,
        "assumption_count": assumption_count,
    }
