"""Normalization validation tests (SPEC 8.3)."""

import json
import tempfile
from pathlib import Path

import pytest

from sm_pipeline.validate.normalization import NormalizationError, validate_normalization


def _write_claims(paper_dir: Path, claims: list) -> None:
    (paper_dir / "claims.json").write_text(json.dumps(claims), encoding="utf-8")


def test_duplicate_claim_ids_raise() -> None:
    """Duplicate claim IDs in a paper raise NormalizationError."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        paper_dir = root / "corpus" / "papers" / "p1"
        paper_dir.mkdir(parents=True)
        _write_claims(
            paper_dir,
            [
                {
                    "id": "c1",
                    "paper_id": "p1",
                    "section": "1",
                    "informal_text": "a",
                    "claim_type": "definition",
                    "status": "unparsed",
                },
                {
                    "id": "c1",
                    "paper_id": "p1",
                    "section": "1",
                    "informal_text": "b",
                    "claim_type": "definition",
                    "status": "unparsed",
                },
            ],
        )
        with pytest.raises(NormalizationError, match="duplicate claim IDs"):
            validate_normalization(root)


def test_duplicate_assumption_ids_raise() -> None:
    """Duplicate assumption IDs in a paper raise NormalizationError."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        paper_dir = root / "corpus" / "papers" / "p1"
        paper_dir.mkdir(parents=True)
        _write_claims(
            paper_dir,
            [
                {
                    "id": "c1",
                    "paper_id": "p1",
                    "section": "1",
                    "informal_text": "x",
                    "claim_type": "definition",
                    "status": "unparsed",
                }
            ],
        )
        (paper_dir / "assumptions.json").write_text(
            json.dumps(
                [
                    {"id": "a1", "paper_id": "p1", "text": "x", "kind": "physical_regime"},
                    {"id": "a1", "paper_id": "p1", "text": "y", "kind": "physical_regime"},
                ]
            ),
            encoding="utf-8",
        )
        with pytest.raises(NormalizationError, match="duplicate assumption IDs"):
            validate_normalization(root)


def test_linked_assumptions_unresolved_raise() -> None:
    """Claim linking to non-existent assumption ID raises NormalizationError."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        paper_dir = root / "corpus" / "papers" / "p1"
        paper_dir.mkdir(parents=True)
        _write_claims(
            paper_dir,
            [
                {
                    "id": "c1",
                    "paper_id": "p1",
                    "section": "1",
                    "informal_text": "x",
                    "claim_type": "definition",
                    "status": "unparsed",
                    "linked_assumptions": ["nonexistent"],
                }
            ],
        )
        (paper_dir / "assumptions.json").write_text(
            json.dumps([{"id": "a1", "paper_id": "p1", "text": "x", "kind": "physical_regime"}]),
            encoding="utf-8",
        )
        with pytest.raises(NormalizationError, match="linked_assumptions references missing ID"):
            validate_normalization(root)


def test_linked_symbols_unresolved_raise() -> None:
    """Claim linking to non-existent symbol ID raises NormalizationError."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        paper_dir = root / "corpus" / "papers" / "p1"
        paper_dir.mkdir(parents=True)
        _write_claims(
            paper_dir,
            [
                {
                    "id": "c1",
                    "paper_id": "p1",
                    "section": "1",
                    "informal_text": "x",
                    "claim_type": "definition",
                    "status": "unparsed",
                    "linked_symbols": ["nonexistent"],
                }
            ],
        )
        (paper_dir / "symbols.json").write_text(
            json.dumps([{"id": "s1", "paper_id": "p1", "raw_latex": "x", "normalized_name": "x"}]),
            encoding="utf-8",
        )
        with pytest.raises(NormalizationError, match="linked_symbols references missing ID"):
            validate_normalization(root)


def test_valid_links_pass() -> None:
    """Unique IDs and resolved links pass."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        paper_dir = root / "corpus" / "papers" / "p1"
        paper_dir.mkdir(parents=True)
        _write_claims(
            paper_dir,
            [
                {
                    "id": "c1",
                    "paper_id": "p1",
                    "section": "1",
                    "informal_text": "x",
                    "claim_type": "definition",
                    "status": "unparsed",
                    "linked_assumptions": ["a1"],
                    "linked_symbols": ["s1"],
                }
            ],
        )
        (paper_dir / "assumptions.json").write_text(
            json.dumps([{"id": "a1", "paper_id": "p1", "text": "x", "kind": "physical_regime"}]),
            encoding="utf-8",
        )
        (paper_dir / "symbols.json").write_text(
            json.dumps([{"id": "s1", "paper_id": "p1", "raw_latex": "x", "normalized_name": "x"}]),
            encoding="utf-8",
        )
        validate_normalization(root)
