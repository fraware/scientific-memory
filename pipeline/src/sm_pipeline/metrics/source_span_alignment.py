"""Source-span alignment: compare corpus claim source_span to reference (gold) spans."""

import json
from pathlib import Path


def _span_equal(a: dict | None, b: dict | None) -> bool:
    """Exact equality of source_span (source_file, start, end)."""
    if a is None and b is None:
        return True
    if not isinstance(a, dict) or not isinstance(b, dict):
        return False
    return (
        a.get("source_file") == b.get("source_file")
        and a.get("start") == b.get("start")
        and a.get("end") == b.get("end")
    )


def _load_json(path: Path) -> list | dict | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def compute_source_span_alignment(repo_root: Path) -> dict:
    """
    For each paper with benchmarks/gold/<paper_id>/source_spans.json, compare
    corpus claim source_spans to reference. source_spans.json format: list of
    { "claim_id": string, "source_span": { source_file, start, end } }.
    Returns alignment_error_count, total_compared, alignment_error_rate; empty when no ref.
    """
    repo_root = repo_root.resolve()
    gold_base = repo_root / "benchmarks" / "gold"
    papers_dir = repo_root / "corpus" / "papers"
    if not gold_base.is_dir() or not papers_dir.is_dir():
        return _empty_result()

    total_compared = 0
    alignment_errors = 0

    for paper_dir in sorted(gold_base.iterdir()):
        if not paper_dir.is_dir():
            continue
        paper_id = paper_dir.name
        ref_path = paper_dir / "source_spans.json"
        if not ref_path.exists():
            continue
        ref_data = _load_json(ref_path)
        if not isinstance(ref_data, list):
            continue
        ref_by_id = {
            r["claim_id"]: r.get("source_span")
            for r in ref_data
            if isinstance(r, dict) and r.get("claim_id")
        }
        claims_path = papers_dir / paper_id / "claims.json"
        corpus_claims = _load_json(claims_path)
        if not isinstance(corpus_claims, list):
            continue
        for c in corpus_claims:
            if not isinstance(c, dict):
                continue
            cid = c.get("id")
            if cid not in ref_by_id:
                continue
            total_compared += 1
            if not _span_equal(c.get("source_span"), ref_by_id[cid]):
                alignment_errors += 1

    if total_compared == 0:
        return _empty_result()
    rate = alignment_errors / total_compared
    return {
        "total_compared": total_compared,
        "alignment_error_count": alignment_errors,
        "alignment_error_rate": round(rate, 4),
    }


def _empty_result() -> dict:
    return {
        "total_compared": 0,
        "alignment_error_count": 0,
        "alignment_error_rate": None,
    }
