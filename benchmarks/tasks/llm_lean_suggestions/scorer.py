"""Benchmark slice: optional llm_lean_proposals.json sidecars (Gate 6 observability)."""

from __future__ import annotations

import json
from pathlib import Path


def run(repo_root: Path) -> dict:
    repo_root = repo_root.resolve()
    papers_dir = repo_root / "corpus" / "papers"
    out: dict = {
        "papers_scanned": 0,
        "llm_lean_proposal_files": 0,
        "lean_proposals_total": 0,
        "lean_proposals_with_replacements": 0,
        "lean_proposals_conversion_ready": 0,
        "by_edit_kind": {
            "new_theorem": 0,
            "proof_repair": 0,
            "lemma_extraction": 0,
        },
    }
    if not papers_dir.is_dir():
        return out

    for paper_dir in sorted(papers_dir.iterdir()):
        if not paper_dir.is_dir():
            continue
        out["papers_scanned"] += 1
        path = paper_dir / "llm_lean_proposals.json"
        if not path.is_file():
            continue
        out["llm_lean_proposal_files"] += 1
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        if not isinstance(data, dict):
            continue
        props = data.get("proposals")
        if not isinstance(props, list):
            continue
        for p in props:
            if not isinstance(p, dict):
                continue
            out["lean_proposals_total"] += 1
            reps = p.get("replacements")
            has_rep = isinstance(reps, list) and len(reps) > 0
            if has_rep:
                out["lean_proposals_with_replacements"] += 1
            tf = (p.get("target_file") or "").strip().replace("\\", "/")
            if has_rep and tf.startswith("formal/") and ".." not in tf:
                out["lean_proposals_conversion_ready"] += 1
            ek = p.get("edit_kind")
            if ek in out["by_edit_kind"]:
                out["by_edit_kind"][str(ek)] += 1
    return out
