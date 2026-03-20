"""Median time from paper intake to first artifact (SPEC 12)."""

import json
from datetime import datetime
from pathlib import Path


def compute_median_intake_time(repo_root: Path) -> dict | None:
    """
    Compute median (and min/max) duration from intake to first_artifact_at.
    Intake = intake_report.json created_at when present; else paper excluded.
    Returns None if no papers with both timestamps; else dict with
    median_seconds, min_seconds, max_seconds, count, paper_ids.
    """
    repo_root = repo_root.resolve()
    papers_dir = repo_root / "corpus" / "papers"
    index_path = repo_root / "corpus" / "index.json"
    if not papers_dir.is_dir() or not index_path.exists():
        return None
    index = json.loads(index_path.read_text(encoding="utf-8"))
    paper_list = index.get("papers") or []
    paper_ids = [p["id"] for p in paper_list if isinstance(p, dict) and p.get("id")]

    durations_seconds: list[float] = []
    contributing_ids: list[str] = []

    for paper_id in paper_ids:
        paper_dir = papers_dir / paper_id
        meta_path = paper_dir / "metadata.json"
        intake_path = paper_dir / "intake_report.json"
        if not meta_path.exists() or not intake_path.exists():
            continue
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            intake_data = json.loads(intake_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        first_at = meta.get("first_artifact_at") if isinstance(meta, dict) else None
        created_at = intake_data.get("created_at") if isinstance(intake_data, dict) else None
        if not first_at or not created_at:
            continue
        try:
            t1 = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
            t2 = datetime.fromisoformat(first_at.replace("Z", "+00:00"))
            delta = (t2 - t1).total_seconds()
            if delta >= 0:
                durations_seconds.append(delta)
                contributing_ids.append(paper_id)
        except (ValueError, TypeError):
            continue

    if not durations_seconds:
        return None
    durations_seconds.sort()
    n = len(durations_seconds)
    median = (
        durations_seconds[n // 2]
        if n % 2
        else ((durations_seconds[n // 2 - 1] + durations_seconds[n // 2]) / 2)
    )
    return {
        "median_seconds": round(median, 2),
        "min_seconds": round(min(durations_seconds), 2),
        "max_seconds": round(max(durations_seconds), 2),
        "count": n,
        "paper_ids": contributing_ids,
    }
