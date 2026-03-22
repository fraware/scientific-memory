"""Unit tests for extraction modes and unresolved-link preservation (trust hardening)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from sm_pipeline.extract.claims import (
    EXTRACTION_MODE_DETERMINISTIC,
    EXTRACTION_MODE_LLM_SIDECAR,
    EXTRACTION_MODE_SCAFFOLD_ONLY,
    extract_claims,
)
from sm_pipeline.extract.normalize import normalize_paper


def _write_minimal_paper(tmp_path: Path, paper_id: str) -> Path:
    paper_dir = tmp_path / "corpus" / "papers" / paper_id
    paper_dir.mkdir(parents=True)
    (paper_dir / "metadata.json").write_text(
        json.dumps(
            {
                "id": paper_id,
                "source": {"path": "source/source.pdf"},
            }
        ),
        encoding="utf-8",
    )
    return paper_dir


def test_scaffold_only_writes_placeholder_when_claims_missing(tmp_path: Path) -> None:
    paper_id = "trust_scaffold_paper"
    _write_minimal_paper(tmp_path, paper_id)
    out = extract_claims(tmp_path, paper_id, mode=EXTRACTION_MODE_SCAFFOLD_ONLY)
    claims_path = tmp_path / "corpus" / "papers" / paper_id / "claims.json"
    assert claims_path.exists()
    claims = json.loads(claims_path.read_text(encoding="utf-8"))
    assert isinstance(claims, list) and len(claims) == 1
    assert out["placeholder_claim_written"] is True
    assert out["extraction_mode"] == EXTRACTION_MODE_SCAFFOLD_ONLY
    run_path = tmp_path / "corpus" / "papers" / paper_id / "extraction_run.json"
    assert run_path.exists()
    run = json.loads(run_path.read_text(encoding="utf-8"))
    assert run["extraction_mode"] == EXTRACTION_MODE_SCAFFOLD_ONLY
    assert run["placeholder_claim_written"] is True


def test_scaffold_only_writes_placeholder_when_claims_empty_array(tmp_path: Path) -> None:
    paper_id = "trust_scaffold_empty"
    paper_dir = _write_minimal_paper(tmp_path, paper_id)
    (paper_dir / "claims.json").write_text("[]", encoding="utf-8")
    out = extract_claims(tmp_path, paper_id, mode=EXTRACTION_MODE_SCAFFOLD_ONLY)
    claims = json.loads((paper_dir / "claims.json").read_text(encoding="utf-8"))
    assert len(claims) == 1
    assert out["placeholder_claim_written"] is True


@pytest.mark.parametrize("mode", [EXTRACTION_MODE_DETERMINISTIC, EXTRACTION_MODE_LLM_SIDECAR])
def test_non_scaffold_modes_do_not_scaffold_placeholder_when_missing(
    tmp_path: Path, mode: str
) -> None:
    paper_id = f"trust_no_scaffold_{mode}"
    _write_minimal_paper(tmp_path, paper_id)
    out = extract_claims(tmp_path, paper_id, mode=mode)
    claims_path = tmp_path / "corpus" / "papers" / paper_id / "claims.json"
    claims = json.loads(claims_path.read_text(encoding="utf-8"))
    assert claims == []
    assert out["placeholder_claim_written"] is False
    assert out["extraction_mode"] == mode
    run_path = tmp_path / "corpus" / "papers" / paper_id / "extraction_run.json"
    assert run_path.exists()
    run = json.loads(run_path.read_text(encoding="utf-8"))
    assert run["extraction_mode"] == mode
    assert run["placeholder_claim_written"] is False


def test_normalize_preserves_unresolved_and_resolves_known_links(tmp_path: Path) -> None:
    paper_id = "trust_norm_links"
    paper_dir = _write_minimal_paper(tmp_path, paper_id)
    (paper_dir / "assumptions.json").write_text(
        json.dumps(
            [
                {
                    "id": "a_ok",
                    "paper_id": paper_id,
                    "text": "ok",
                    "kind": "domain_restriction",
                }
            ]
        ),
        encoding="utf-8",
    )
    (paper_dir / "symbols.json").write_text(
        json.dumps(
            [
                {
                    "id": "s_ok",
                    "paper_id": paper_id,
                    "raw_latex": "x",
                    "normalized_name": "x",
                }
            ]
        ),
        encoding="utf-8",
    )
    (paper_dir / "claims.json").write_text(
        json.dumps(
            [
                {
                    "id": "c1",
                    "paper_id": paper_id,
                    "section": "1",
                    "informal_text": "t",
                    "claim_type": "definition",
                    "status": "unparsed",
                    "linked_assumptions": ["a_ok", "ghost_a"],
                    "linked_symbols": ["s_ok", "ghost_s"],
                    "linked_assumptions_unresolved": ["ghost_a"],
                    "linked_symbols_unresolved": ["ghost_s"],
                }
            ]
        ),
        encoding="utf-8",
    )
    report = normalize_paper(tmp_path, paper_id)
    claims = json.loads((paper_dir / "claims.json").read_text(encoding="utf-8"))
    c0 = claims[0]
    assert c0["linked_assumptions"] == ["a_ok"]
    assert c0["linked_symbols"] == ["s_ok"]
    assert c0["linked_assumptions_unresolved"] == ["ghost_a"]
    assert c0["linked_symbols_unresolved"] == ["ghost_s"]
    assert report["unresolved_assumption_links_preserved"] == 1
    assert report["unresolved_symbol_links_preserved"] == 1
    assert report["unresolved_claim_links"] == [
        {
            "claim_id": "c1",
            "linked_assumptions_unresolved": ["ghost_a"],
            "linked_symbols_unresolved": ["ghost_s"],
        }
    ]


def test_normalize_clears_unresolved_fields_when_all_resolve(tmp_path: Path) -> None:
    paper_id = "trust_norm_all_resolved"
    paper_dir = _write_minimal_paper(tmp_path, paper_id)
    (paper_dir / "assumptions.json").write_text(
        json.dumps([{"id": "a1", "paper_id": paper_id, "text": "t", "kind": "domain_restriction"}]),
        encoding="utf-8",
    )
    (paper_dir / "symbols.json").write_text(
        json.dumps([{"id": "s1", "paper_id": paper_id, "raw_latex": "x", "normalized_name": "x"}]),
        encoding="utf-8",
    )
    (paper_dir / "claims.json").write_text(
        json.dumps(
            [
                {
                    "id": "c1",
                    "paper_id": paper_id,
                    "section": "1",
                    "informal_text": "t",
                    "claim_type": "definition",
                    "status": "unparsed",
                    "linked_assumptions": ["a1"],
                    "linked_symbols": ["s1"],
                }
            ]
        ),
        encoding="utf-8",
    )
    normalize_paper(tmp_path, paper_id)
    claims = json.loads((paper_dir / "claims.json").read_text(encoding="utf-8"))
    assert "linked_assumptions_unresolved" not in claims[0]
    assert "linked_symbols_unresolved" not in claims[0]
