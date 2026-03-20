"""Tests for benchmarks/tasks/gold/scorer.py (loaded like the benchmark runner)."""

import importlib.util
import json
import sys
from pathlib import Path


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _load_gold_scorer():
    path = _repo_root() / "benchmarks" / "tasks" / "gold" / "scorer.py"
    spec = importlib.util.spec_from_file_location(
        "sm_pipeline_tests_gold_scorer",
        path,
    )
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def test_gold_scorer_perfect_match_and_alignment(tmp_path: Path) -> None:
    mod = _load_gold_scorer()
    span = {
        "source_file": "source/x.pdf",
        "start": {"page": 1, "offset": 0},
        "end": {"page": 1, "offset": 10},
    }
    claim = {
        "id": "c1",
        "paper_id": "p1",
        "source_span": span,
    }
    pdir = tmp_path / "corpus" / "papers" / "p1"
    pdir.mkdir(parents=True)
    (pdir / "claims.json").write_text(json.dumps([claim]), encoding="utf-8")
    gdir = tmp_path / "benchmarks" / "gold" / "p1"
    gdir.mkdir(parents=True)
    (gdir / "claims.json").write_text(json.dumps([claim]), encoding="utf-8")
    (gdir / "source_spans.json").write_text(
        json.dumps([{"claim_id": "c1", "source_span": span}]),
        encoding="utf-8",
    )
    out = mod.run(tmp_path)
    assert out["papers_with_gold"] == 1
    assert out["gold_claim_precision"] == 1.0
    assert out["gold_claim_recall"] == 1.0
    assert out["gold_claim_f1"] == 1.0
    assert out["source_span_total_compared"] == 1
    assert out["source_span_alignment_error_count"] == 0
    assert out["source_span_alignment_error_rate"] == 0.0


def test_gold_scorer_alignment_mismatch(tmp_path: Path) -> None:
    mod = _load_gold_scorer()
    span_corpus = {
        "source_file": "source/x.pdf",
        "start": {"page": 1, "offset": 0},
        "end": {"page": 1, "offset": 10},
    }
    span_gold = {
        "source_file": "source/x.pdf",
        "start": {"page": 1, "offset": 0},
        "end": {"page": 1, "offset": 99},
    }
    claim = {"id": "c1", "paper_id": "p1", "source_span": span_corpus}
    pdir = tmp_path / "corpus" / "papers" / "p1"
    pdir.mkdir(parents=True)
    (pdir / "claims.json").write_text(json.dumps([claim]), encoding="utf-8")
    gdir = tmp_path / "benchmarks" / "gold" / "p1"
    gdir.mkdir(parents=True)
    (gdir / "claims.json").write_text(json.dumps([claim]), encoding="utf-8")
    (gdir / "source_spans.json").write_text(
        json.dumps([{"claim_id": "c1", "source_span": span_gold}]),
        encoding="utf-8",
    )
    out = mod.run(tmp_path)
    assert out["source_span_alignment_error_count"] == 1
    assert out["source_span_alignment_error_rate"] == 1.0
