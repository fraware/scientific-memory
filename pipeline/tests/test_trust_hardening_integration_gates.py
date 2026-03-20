"""Integration tests for warn-only dependency bootstrap and LLM suggestion sidecars."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from sm_pipeline.publish.manifest import publish_manifest
from sm_pipeline.validate.gate_engine import run_all_gates
from sm_pipeline.validate.graph import validate_dependency_graph_bootstrap_warn
from sm_pipeline.validate.llm_proposals import validate_llm_proposal_sidecars_warn


REPO_ROOT = Path(__file__).resolve().parents[2]


def _paper_with_bootstrap_warn_scenario(root: Path, paper_id: str) -> None:
    paper_dir = root / "corpus" / "papers" / paper_id
    paper_dir.mkdir(parents=True)
    (paper_dir / "metadata.json").write_text(
        json.dumps({"id": paper_id, "title": "T", "source": {"path": "s.pdf"}}),
        encoding="utf-8",
    )
    (paper_dir / "claims.json").write_text(
        json.dumps(
            [
                {
                    "id": "c1",
                    "paper_id": paper_id,
                    "section": "1",
                    "informal_text": "a",
                    "claim_type": "lemma",
                    "status": "machine_checked",
                    "source_span": {
                        "source_file": "s.pdf",
                        "start": {"page": 1, "offset": 0},
                        "end": {"page": 1, "offset": 1},
                    },
                },
                {
                    "id": "c2",
                    "paper_id": paper_id,
                    "section": "2",
                    "informal_text": "b",
                    "claim_type": "lemma",
                    "status": "unparsed",
                    "source_span": {
                        "source_file": "s.pdf",
                        "start": {"page": 1, "offset": 2},
                        "end": {"page": 1, "offset": 3},
                    },
                },
            ]
        ),
        encoding="utf-8",
    )
    (paper_dir / "theorem_cards.json").write_text(
        json.dumps(
            [
                {
                    "id": f"{paper_id}_card_a",
                    "claim_id": "c1",
                    "lean_decl": "X.a",
                    "file_path": "",
                    "proof_status": "machine_checked",
                    "verification_boundary": "fully_machine_checked",
                    "dependency_ids": [],
                    "executable_links": [],
                },
                {
                    "id": f"{paper_id}_card_b",
                    "claim_id": "c2",
                    "lean_decl": "X.b",
                    "file_path": "",
                    "proof_status": "mapped",
                    "verification_boundary": "human_review_only",
                    "dependency_ids": [],
                    "executable_links": [],
                },
            ]
        ),
        encoding="utf-8",
    )


def test_dependency_graph_bootstrap_warn_multi_card_empty_deps_machine_checked(
    tmp_path: Path,
) -> None:
    _paper_with_bootstrap_warn_scenario(tmp_path, "gate_bootstrap_warn")
    warnings = validate_dependency_graph_bootstrap_warn(tmp_path)
    assert len(warnings) == 1
    assert "dependency_extraction_method is bootstrap regex" in warnings[0]


def test_llm_proposal_sidecar_invalid_json_warns(tmp_path: Path) -> None:
    shutil.copytree(REPO_ROOT / "schemas", tmp_path / "schemas")
    paper_dir = tmp_path / "corpus" / "papers" / "llm_bad_sidecar"
    paper_dir.mkdir(parents=True)
    (paper_dir / "llm_claim_proposals.json").write_text("not valid json{{{", encoding="utf-8")
    warnings = validate_llm_proposal_sidecars_warn(tmp_path)
    assert warnings
    assert any("llm_claim_proposals.json" in w for w in warnings)


def test_llm_proposal_sidecar_schema_violation_warns(tmp_path: Path) -> None:
    shutil.copytree(REPO_ROOT / "schemas", tmp_path / "schemas")
    paper_dir = tmp_path / "corpus" / "papers" / "llm_schema_bad"
    paper_dir.mkdir(parents=True)
    (paper_dir / "suggested_assumptions.json").write_text(
        json.dumps({"not": "a valid suggested assumptions payload"}),
        encoding="utf-8",
    )
    warnings = validate_llm_proposal_sidecars_warn(tmp_path)
    assert warnings
    assert any("suggested_assumptions.json" in w for w in warnings)


def test_publish_manifest_sets_dependency_extraction_method(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("SM_PUBLISH_REUSE_MANIFEST_GRAPHS", raising=False)
    paper_id = "gate_dep_method"
    paper_dir = tmp_path / "corpus" / "papers" / paper_id
    paper_dir.mkdir(parents=True)
    (paper_dir / "claims.json").write_text(
        json.dumps(
            [
                {
                    "id": "c1",
                    "paper_id": paper_id,
                    "section": "1",
                    "informal_text": "x",
                    "claim_type": "definition",
                    "status": "unparsed",
                    "source_span": {
                        "source_file": "source/source.pdf",
                        "start": {"page": 1, "offset": 0},
                        "end": {"page": 1, "offset": 10},
                    },
                }
            ]
        ),
        encoding="utf-8",
    )
    (paper_dir / "mapping.json").write_text(
        json.dumps({"namespace": "TestNs", "claim_to_decl": {"c1": "Thm1"}}),
        encoding="utf-8",
    )
    publish_manifest(tmp_path, paper_id)
    cards = json.loads((paper_dir / "theorem_cards.json").read_text(encoding="utf-8"))
    assert len(cards) == 1
    assert cards[0].get("dependency_extraction_method") == "lean_source_regex_tier0"


def test_run_all_gates_records_dependency_bootstrap_when_present() -> None:
    report = run_all_gates(REPO_ROOT)
    bootstrap_steps = [s for s in report.steps if s.check_id == "dependency_graph_bootstrap"]
    assert bootstrap_steps
    assert all(s.status == "warn" for s in bootstrap_steps)