"""Tests for Lean source-based dependency extraction (theorem card dependency_ids)."""

from pathlib import Path

from sm_pipeline.formalize.lean_deps import (
    _find_referenced_declarations,
    _parse_lean_declarations_and_bodies,
    _short_name,
    extract_dependency_ids_for_cards,
)


def test_short_name():
    assert (
        _short_name("ScientificMemory.Chemistry.Adsorption.Langmuir1918.langmuir_sub_one")
        == "langmuir_sub_one"
    )
    assert _short_name("langmuir_isotherm_one") == "langmuir_isotherm_one"
    assert _short_name("") == ""


def test_parse_lean_declarations_and_bodies():
    content = """
theorem foo (n : Nat) : n = n := rfl
theorem bar : 1 = 1 := (foo 1).symm
"""
    pairs = _parse_lean_declarations_and_bodies(content)
    assert len(pairs) == 2
    names = [p[0] for p in pairs]
    assert "foo" in names and "bar" in names
    bar_body = next(p[1] for p in pairs if p[0] == "bar")
    assert "foo" in bar_body


def test_find_referenced_declarations():
    body = " (langmuir_sub_one K P h).symm"
    refs = _find_referenced_declarations(body, {"langmuir_sub_one", "other"})
    assert refs == {"langmuir_sub_one"}
    refs2 = _find_referenced_declarations(
        " LangmuirCoverage K P", {"LangmuirCoverage", "langmuir_isotherm"}
    )
    assert "LangmuirCoverage" in refs2


def test_extract_dependency_ids_for_cards_isotherm_alias_symbol(tmp_path):
    """Mentioning RHS symbol (e.g. FreundlichIsotherm) links to local def card."""
    repo = tmp_path
    lean_file = (
        repo / "formal" / "ScientificMemory" / "Chemistry" / "Adsorption" / "Freundlich1906.lean"
    )
    lean_file.parent.mkdir(parents=True, exist_ok=True)
    lean_file.write_text(
        """
namespace ScientificMemory.Chemistry.Adsorption.Freundlich1906
noncomputable def freundlich_isotherm := FreundlichIsotherm
theorem freundlich_nonneg (k c n : ℝ) : 0 ≤ FreundlichIsotherm k c n := by
  unfold FreundlichIsotherm
  exact le_refl 0
end ScientificMemory.Chemistry.Adsorption.Freundlich1906
""",
        encoding="utf-8",
    )
    cards = [
        {
            "id": "card_def",
            "lean_decl": "Sm.Freundlich1906.freundlich_isotherm",
            "file_path": "formal/ScientificMemory/Chemistry/Adsorption/Freundlich1906.lean",
        },
        {
            "id": "card_th",
            "lean_decl": "Sm.Freundlich1906.freundlich_nonneg",
            "file_path": "formal/ScientificMemory/Chemistry/Adsorption/Freundlich1906.lean",
        },
    ]
    out = extract_dependency_ids_for_cards(repo, "test_paper", cards)
    th = next(c for c in out if c["id"] == "card_th")
    assert "card_def" in th["dependency_ids"]


def test_extract_dependency_ids_for_cards_populates_deps(tmp_path):
    """Extract adds dependency_ids when Lean source references same-file declarations."""
    repo = tmp_path
    lean_file = (
        repo / "formal" / "ScientificMemory" / "Chemistry" / "Adsorption" / "Langmuir1918.lean"
    )
    lean_file.parent.mkdir(parents=True, exist_ok=True)
    lean_file.write_text(
        """
namespace ScientificMemory.Chemistry.Adsorption.Langmuir1918
theorem langmuir_sub_one (K P : ℝ) (h : 1 + K * P ≠ 0) :
    (1 : ℝ) - 1 = 0 := by ring
theorem langmuir_recip_denom (K P : ℝ) (h : 1 + K * P ≠ 0) :
    1 / (1 + K * P) = 1 - 0 := (langmuir_sub_one K P h).symm
end ScientificMemory.Chemistry.Adsorption.Langmuir1918
""",
        encoding="utf-8",
    )
    cards = [
        {
            "id": "card_001",
            "lean_decl": "Sm.Langmuir1918.langmuir_sub_one",
            "file_path": "formal/ScientificMemory/Chemistry/Adsorption/Langmuir1918.lean",
        },
        {
            "id": "card_002",
            "lean_decl": "Sm.Langmuir1918.langmuir_recip_denom",
            "file_path": "formal/ScientificMemory/Chemistry/Adsorption/Langmuir1918.lean",
        },
    ]
    out = extract_dependency_ids_for_cards(repo, "test_paper", cards)
    card_001 = next(c for c in out if c["id"] == "card_001")
    card_002 = next(c for c in out if c["id"] == "card_002")
    assert card_001["dependency_ids"] == []
    assert card_002["dependency_ids"] == ["card_001"]


def test_extract_dependency_ids_for_cards_empty_cards():
    out = extract_dependency_ids_for_cards(Path("."), "x", [])
    assert out == []


def test_extract_dependency_ids_for_cards_missing_file(tmp_path):
    """When Lean file is missing, cards are unchanged (dependency_ids not set or remain)."""
    cards = [
        {
            "id": "c1",
            "lean_decl": "X.foo",
            "file_path": "formal/Nonexistent.lean",
            "dependency_ids": [],
        },
    ]
    out = extract_dependency_ids_for_cards(tmp_path, "p", cards)
    assert out[0].get("dependency_ids") == []
