"""MCP data-path tests against fixture corpus files."""

import json
from pathlib import Path

from sm_pipeline import mcp_server


def _write_minimal_paper(root: Path) -> None:
    paper = root / "corpus" / "papers" / "p1"
    paper.mkdir(parents=True)
    (root / "corpus" / "index.json").write_text(
        json.dumps({"version": "0.1", "papers": [{"id": "p1", "title": "P1", "year": 2024, "domain": "other"}]}),
        encoding="utf-8",
    )
    (paper / "manifest.json").write_text(
        json.dumps(
            {
                "paper_id": "p1",
                "declaration_index": ["ScientificMemory.P1.d1"],
                "dependency_graph": [{"from": "p1_card_001", "to": "ScientificMemory.P1.d1"}],
            }
        ),
        encoding="utf-8",
    )
    (paper / "theorem_cards.json").write_text(
        json.dumps(
            [
                {
                    "id": "p1_card_001",
                    "claim_id": "p1_claim_001",
                    "lean_decl": "ScientificMemory.P1.d1",
                    "file_path": "formal/ScientificMemory/P1.lean",
                    "proof_status": "machine_checked",
                    "verification_boundary": "fully_machine_checked",
                    "reviewer_status": "accepted",
                    "dependency_ids": [],
                    "executable_links": [],
                }
            ]
        ),
        encoding="utf-8",
    )


def test_list_declarations_for_paper_reads_manifest_and_cards(tmp_path: Path, monkeypatch) -> None:
    _write_minimal_paper(tmp_path)
    monkeypatch.chdir(tmp_path)
    out = mcp_server._list_declarations_for_paper("p1")
    assert any(d.get("source") == "manifest" for d in out)
    assert any(d.get("source") == "theorem_cards" for d in out)


def test_dependency_graph_for_declaration_returns_card_and_graph(tmp_path: Path, monkeypatch) -> None:
    _write_minimal_paper(tmp_path)
    monkeypatch.chdir(tmp_path)
    out = mcp_server._get_dependency_graph_for_declaration("p1", "ScientificMemory.P1.d1")
    assert out["paper_id"] == "p1"
    assert out["cards"]
    assert out["manifest_dependency_graph"]
