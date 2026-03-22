"""Regression tests for deepened chem_dilution_reference slice."""

from __future__ import annotations

import json
from pathlib import Path


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def test_chem_dilution_has_two_machine_checked_mapped_claims() -> None:
    root = _repo_root()
    paper = root / "corpus" / "papers" / "chem_dilution_reference"
    enc = "utf-8"
    claims = json.loads((paper / "claims.json").read_text(encoding=enc))
    mapping = json.loads((paper / "mapping.json").read_text(encoding=enc))
    assumptions = json.loads((paper / "assumptions.json").read_text(encoding=enc))
    symbols = json.loads((paper / "symbols.json").read_text(encoding=enc))
    cards = json.loads((paper / "theorem_cards.json").read_text(encoding=enc))

    assert len(claims) == 2
    assert all(c.get("status") == "machine_checked" for c in claims)
    assert all(c.get("linked_assumptions") for c in claims)
    assert all(c.get("linked_symbols") for c in claims)

    ctd = mapping.get("claim_to_decl") or {}
    assert len(ctd) == 2
    assert ctd.get("chem_dilution_reference_claim_002") == "conc_from_fixed_amount"

    assert len(assumptions) >= 2
    assert len(symbols) >= 5
    assert len(cards) == 2
    decls = {c.get("lean_decl") for c in cards if isinstance(c, dict)}
    want = "ScientificMemory.Chemistry.Solutions.DilutionRef.conc_from_fixed_amount"
    assert want in decls
