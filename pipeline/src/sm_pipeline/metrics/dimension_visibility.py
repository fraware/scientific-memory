"""8.3 Dimension visibility: symbols with/without dimensional_metadata."""

import json
from pathlib import Path


def compute_dimension_visibility(repo_root: Path) -> dict:
    """
    Report symbols that have dimensional_metadata vs those that do not.
    Visibility only; no schema change. Supports unit/dimension tagging triage.
    """
    repo_root = repo_root.resolve()
    papers_dir = repo_root / "corpus" / "papers"
    index_path = repo_root / "corpus" / "index.json"
    if not papers_dir.is_dir() or not index_path.exists():
        return _empty_result()

    index = json.loads(index_path.read_text(encoding="utf-8"))
    papers = index.get("papers") or []
    paper_ids = [p["id"] for p in papers if isinstance(p, dict) and p.get("id")]

    with_meta: list[dict] = []
    without_meta: list[dict] = []

    for paper_id in paper_ids:
        paper_dir = papers_dir / paper_id
        symbols_path = paper_dir / "symbols.json"
        if not symbols_path.exists():
            continue
        try:
            data = json.loads(symbols_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        if not isinstance(data, list):
            continue
        for s in data:
            if not isinstance(s, dict):
                continue
            sid = s.get("id", "")
            meta = s.get("dimensional_metadata")
            entry = {"paper_id": paper_id, "symbol_id": sid}
            has_meta = (
                meta
                and isinstance(meta, dict)
                and (meta.get("unit") or meta.get("dimension") or meta.get("kind"))
            )
            if has_meta:
                with_meta.append(entry)
            else:
                without_meta.append(entry)

    return {
        "symbols_with_dimensional_metadata": with_meta,
        "symbols_without_dimensional_metadata": without_meta,
        "with_count": len(with_meta),
        "without_count": len(without_meta),
    }


def _empty_result() -> dict:
    return {
        "symbols_with_dimensional_metadata": [],
        "symbols_without_dimensional_metadata": [],
        "with_count": 0,
        "without_count": 0,
    }
