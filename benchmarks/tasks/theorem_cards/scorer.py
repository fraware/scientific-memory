"""Theorem card benchmark: declaration and proof-status metrics with per-paper slices."""

import json
from pathlib import Path


def run(repo_root: Path) -> dict:
    """Compute theorem-card metrics from manifests. Returns aggregates and per_paper quality slices."""
    papers_dir = repo_root / "corpus" / "papers"
    if not papers_dir.is_dir():
        return {
            "paper_count": 0,
            "declaration_count": 0,
            "machine_checked_count": 0,
            "per_paper": [],
        }

    paper_count = 0
    declaration_count = 0
    machine_checked_count = 0
    per_paper: list[dict] = []

    for paper_dir in sorted(papers_dir.iterdir()):
        if not paper_dir.is_dir():
            continue
        manifest_path = paper_dir / "manifest.json"
        if not manifest_path.exists():
            continue
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        if not isinstance(manifest, dict):
            continue
        paper_id = paper_dir.name
        paper_count += 1
        decl_index = manifest.get("declaration_index") or []
        decls = len(decl_index) if isinstance(decl_index, list) else 0
        coverage = manifest.get("coverage_metrics") or {}
        mc = int(coverage.get("machine_checked_count") or 0) if isinstance(coverage, dict) else 0
        declaration_count += decls
        machine_checked_count += mc
        per_paper.append({
            "paper_id": paper_id,
            "declaration_count": decls,
            "machine_checked_count": mc,
        })

    return {
        "paper_count": paper_count,
        "declaration_count": declaration_count,
        "machine_checked_count": machine_checked_count,
        "per_paper": per_paper,
    }
