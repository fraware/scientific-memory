"""Integration tests for MCP server using real corpus structure (when available)."""

import json
from pathlib import Path

import pytest

from sm_pipeline import mcp_server


def test_mcp_list_declarations_real_corpus() -> None:
    """Test list_declarations_for_paper with actual corpus if present."""
    repo = Path(__file__).resolve().parents[2]
    langmuir_dir = repo / "corpus" / "papers" / "langmuir_1918_adsorption"
    if not langmuir_dir.is_dir():
        pytest.skip("corpus not present (langmuir_1918_adsorption)")

    # Use monkeypatch to set cwd to repo root so _repo_root() finds corpus
    import os

    original_cwd = os.getcwd()
    try:
        os.chdir(str(repo))
        out = mcp_server._list_declarations_for_paper("langmuir_1918_adsorption")
        assert isinstance(out, list)
        assert len(out) > 0
        # Check structure - items from manifest have "source": "manifest" (no file_path),
        # items from theorem_cards have file_path, proof_status, claim_id
        for decl in out:
            assert "lean_decl" in decl
            assert "source" in decl
            if decl.get("source") == "theorem_cards":
                assert "file_path" in decl
                assert "proof_status" in decl
    finally:
        os.chdir(original_cwd)


def test_mcp_get_dependency_graph_real_corpus() -> None:
    """Test get_dependency_graph_for_declaration with actual corpus if present."""
    repo = Path(__file__).resolve().parents[2]
    langmuir_dir = repo / "corpus" / "papers" / "langmuir_1918_adsorption"
    if not langmuir_dir.is_dir():
        pytest.skip("corpus not present (langmuir_1918_adsorption)")

    # Read a real declaration from theorem_cards
    cards_path = langmuir_dir / "theorem_cards.json"
    if not cards_path.exists():
        pytest.skip("theorem_cards.json not present")
    cards = json.loads(cards_path.read_text(encoding="utf-8"))
    if not cards or not isinstance(cards, list):
        pytest.skip("no theorem cards found")
    first_card = cards[0]
    lean_decl = first_card.get("lean_decl")
    if not lean_decl:
        pytest.skip("no lean_decl in first card")

    import os

    original_cwd = os.getcwd()
    try:
        os.chdir(str(repo))
        out = mcp_server._get_dependency_graph_for_declaration(
            "langmuir_1918_adsorption", lean_decl
        )
        assert isinstance(out, dict)
        assert "declaration" in out or "card" in out or "dependency_ids" in out
    finally:
        os.chdir(original_cwd)
