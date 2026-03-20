"""Mapping benchmark: claim-to-declaration coverage."""

import json
from pathlib import Path


def run(repo_root: Path) -> dict:
    """Compute mapping metrics over corpus. Returns a dict for the report."""
    papers_dir = repo_root / "corpus" / "papers"
    if not papers_dir.is_dir():
        return {"paper_count": 0, "mapped_claims": 0, "total_claims": 0}

    paper_count = 0
    mapped_claims = 0
    total_claims = 0

    for paper_dir in sorted(papers_dir.iterdir()):
        if not paper_dir.is_dir():
            continue
        claims_path = paper_dir / "claims.json"
        mapping_path = paper_dir / "mapping.json"
        if not claims_path.exists() or not mapping_path.exists():
            continue
        try:
            claims = json.loads(claims_path.read_text(encoding="utf-8"))
            mapping = json.loads(mapping_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        if not isinstance(claims, list):
            continue
        paper_count += 1
        claim_to_decl = mapping.get("claim_to_decl") if isinstance(mapping, dict) else {}
        if not isinstance(claim_to_decl, dict):
            claim_to_decl = {}
        total_claims += len(claims)
        for c in claims:
            if isinstance(c, dict) and claim_to_decl.get(str(c.get("id"))):
                mapped_claims += 1

    return {
        "paper_count": paper_count,
        "mapped_claims": mapped_claims,
        "total_claims": total_claims,
    }
