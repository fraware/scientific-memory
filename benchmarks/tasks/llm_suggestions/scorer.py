"""Benchmark slice: optional LLM/suggestion sidecars and unresolved-link visibility (Gate 6 anchor)."""

from __future__ import annotations

import json
from pathlib import Path


def run(repo_root: Path) -> dict:
    repo_root = repo_root.resolve()
    papers_dir = repo_root / "corpus" / "papers"
    out: dict = {
        "papers_scanned": 0,
        "llm_claim_proposal_files": 0,
        "llm_mapping_proposal_files": 0,
        "suggested_assumptions_files": 0,
        "suggested_symbols_files": 0,
        "suggested_mapping_files": 0,
        "canonical_claims_unresolved_assumption_links": 0,
        "canonical_claims_unresolved_symbol_links": 0,
    }
    if not papers_dir.is_dir():
        return out

    for paper_dir in sorted(papers_dir.iterdir()):
        if not paper_dir.is_dir():
            continue
        out["papers_scanned"] += 1
        if (paper_dir / "llm_claim_proposals.json").is_file():
            out["llm_claim_proposal_files"] += 1
        if (paper_dir / "llm_mapping_proposals.json").is_file():
            out["llm_mapping_proposal_files"] += 1
        if (paper_dir / "suggested_assumptions.json").is_file():
            out["suggested_assumptions_files"] += 1
        if (paper_dir / "suggested_symbols.json").is_file():
            out["suggested_symbols_files"] += 1
        if (paper_dir / "suggested_mapping.json").is_file():
            out["suggested_mapping_files"] += 1

        claims_path = paper_dir / "claims.json"
        if not claims_path.exists():
            continue
        try:
            claims = json.loads(claims_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        if not isinstance(claims, list):
            continue
        for c in claims:
            if not isinstance(c, dict):
                continue
            out["canonical_claims_unresolved_assumption_links"] += len(
                c.get("linked_assumptions_unresolved") or []
            )
            out["canonical_claims_unresolved_symbol_links"] += len(
                c.get("linked_symbols_unresolved") or []
            )
    return out
