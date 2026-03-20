"""Tests for source-span alignment vs gold reference."""

import json
from pathlib import Path

from sm_pipeline.metrics.source_span_alignment import compute_source_span_alignment


def _span(page: int, start_off: int, end_off: int) -> dict:
    return {
        "source_file": "source/source.pdf",
        "start": {"page": page, "offset": start_off},
        "end": {"page": page, "offset": end_off},
    }


def test_alignment_empty_when_no_gold(tmp_path: Path) -> None:
    (tmp_path / "corpus" / "papers").mkdir(parents=True)
    r = compute_source_span_alignment(tmp_path)
    assert r["total_compared"] == 0
    assert r["alignment_error_rate"] is None


def test_alignment_matching_spans(tmp_path: Path) -> None:
    span = _span(1, 0, 50)
    claims = [
        {
            "id": "c1",
            "source_span": span,
        }
    ]
    ref = [{"claim_id": "c1", "source_span": span}]
    _layout_paper(tmp_path, "p1", claims, ref)
    r = compute_source_span_alignment(tmp_path)
    assert r["total_compared"] == 1
    assert r["alignment_error_count"] == 0
    assert r["alignment_error_rate"] == 0.0


def test_alignment_mismatch(tmp_path: Path) -> None:
    claims = [{"id": "c1", "source_span": _span(1, 0, 50)}]
    ref = [{"claim_id": "c1", "source_span": _span(1, 0, 99)}]
    _layout_paper(tmp_path, "p1", claims, ref)
    r = compute_source_span_alignment(tmp_path)
    assert r["total_compared"] == 1
    assert r["alignment_error_count"] == 1
    assert r["alignment_error_rate"] == 1.0


def test_alignment_skips_claim_not_in_reference(tmp_path: Path) -> None:
    claims = [
        {"id": "c1", "source_span": _span(1, 0, 1)},
        {"id": "c2", "source_span": _span(1, 2, 3)},
    ]
    ref = [{"claim_id": "c1", "source_span": _span(1, 0, 1)}]
    _layout_paper(tmp_path, "p1", claims, ref)
    r = compute_source_span_alignment(tmp_path)
    assert r["total_compared"] == 1
    assert r["alignment_error_count"] == 0


def test_alignment_malformed_reference_list_skipped(tmp_path: Path) -> None:
    gold = tmp_path / "benchmarks" / "gold" / "p1"
    gold.mkdir(parents=True)
    (gold / "source_spans.json").write_text('"not-a-list"', encoding="utf-8")
    paper = tmp_path / "corpus" / "papers" / "p1"
    paper.mkdir(parents=True)
    (paper / "claims.json").write_text(
        json.dumps([{"id": "c1", "source_span": _span(1, 0, 1)}]),
        encoding="utf-8",
    )
    r = compute_source_span_alignment(tmp_path)
    assert r["total_compared"] == 0
    assert r["alignment_error_rate"] is None


def _layout_paper(
    root: Path, paper_id: str, claims: list, ref_spans: list
) -> None:
    pdir = root / "corpus" / "papers" / paper_id
    pdir.mkdir(parents=True)
    (pdir / "claims.json").write_text(json.dumps(claims), encoding="utf-8")
    gdir = root / "benchmarks" / "gold" / paper_id
    gdir.mkdir(parents=True)
    (gdir / "source_spans.json").write_text(json.dumps(ref_spans), encoding="utf-8")
