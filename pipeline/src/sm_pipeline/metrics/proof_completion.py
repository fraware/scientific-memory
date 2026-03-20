"""Proof completion rate from manifest coverage_metrics (SPEC 12)."""

import json
from pathlib import Path


def compute_proof_completion(repo_root: Path) -> dict:
    """
    Aggregate coverage_metrics across all papers: total mapped claims,
    total machine-checked, proof_completion_rate (machine_checked / mapped when
    mapped > 0). Declaration count from manifest declaration_index.
    """
    repo_root = repo_root.resolve()
    papers_dir = repo_root / "corpus" / "papers"
    index_path = repo_root / "corpus" / "index.json"
    if not papers_dir.is_dir() or not index_path.exists():
        return _empty_result()
    index = json.loads(index_path.read_text(encoding="utf-8"))
    paper_list = index.get("papers") or []
    paper_ids = [p["id"] for p in paper_list if isinstance(p, dict) and p.get("id")]

    total_mapped = 0
    total_machine_checked = 0
    total_declarations = 0
    by_paper: dict[str, dict] = {}

    for paper_id in paper_ids:
        manifest_path = papers_dir / paper_id / "manifest.json"
        if not manifest_path.exists():
            continue
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        if not isinstance(manifest, dict):
            continue
        metrics = manifest.get("coverage_metrics") or {}
        mapped = int(metrics.get("mapped_claim_count") or 0)
        machine_checked = int(metrics.get("machine_checked_count") or 0)
        decl_index = manifest.get("declaration_index") or []
        decl_count = len(decl_index) if isinstance(decl_index, list) else 0

        total_mapped += mapped
        total_machine_checked += machine_checked
        total_declarations += decl_count
        rate = (machine_checked / mapped) if mapped else 0.0
        by_paper[paper_id] = {
            "mapped_claim_count": mapped,
            "machine_checked_count": machine_checked,
            "declaration_count": decl_count,
            "proof_completion_rate": round(rate, 4),
        }

    proof_completion_rate = (total_machine_checked / total_mapped) if total_mapped else 0.0
    milestone_3_target = 40
    return {
        "total_mapped_claims": total_mapped,
        "total_machine_checked": total_machine_checked,
        "total_declarations": total_declarations,
        "proof_completion_rate": round(proof_completion_rate, 4),
        "papers": by_paper,
        "milestone_3_target": milestone_3_target,
        "milestone_3_current": total_machine_checked,
        "milestone_3_progress_ratio": round(total_machine_checked / milestone_3_target, 4)
        if milestone_3_target
        else 0.0,
    }


def _empty_result() -> dict:
    return {
        "total_mapped_claims": 0,
        "total_machine_checked": 0,
        "total_declarations": 0,
        "proof_completion_rate": 0.0,
        "papers": {},
        "milestone_3_target": 40,
        "milestone_3_current": 0,
        "milestone_3_progress_ratio": 0.0,
    }
