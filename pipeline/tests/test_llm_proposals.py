"""LLM proposal generation, apply merge, and sidecar validation (no live API)."""

from __future__ import annotations

import json
from pathlib import Path

from sm_pipeline.llm.apply_proposals import (
    preview_apply_claim_proposals,
    preview_apply_mapping_proposals,
)
from sm_pipeline.llm.json_extract import extract_json_object
from sm_pipeline.llm.proposals_claims import generate_llm_claim_proposals
from sm_pipeline.llm.provider import FakeLLMProvider, LLMMessage
from sm_pipeline.validate.llm_proposals import validate_llm_proposal_sidecars_warn


def test_extract_json_object_from_fence() -> None:
    raw = 'Here:\n```json\n{"a": 1}\n```'
    assert extract_json_object(raw) == {"a": 1}


def test_extract_json_object_with_unescaped_control_char() -> None:
    raw = "{\n  \"a\": \"hello\tworld\"\n}"
    assert extract_json_object(raw) == {"a": "hello\tworld"}


def test_fake_provider_complete() -> None:
    p = FakeLLMProvider(reply="hi", model="m")
    r = p.complete([LLMMessage(role="user", content="x")], model="other")
    assert r.text == "hi"
    assert r.model == "m"


def test_generate_llm_claim_proposals_fake(tmp_path: Path) -> None:
    paper_id = "p_test"
    paper_dir = tmp_path / "corpus" / "papers" / paper_id
    paper_dir.mkdir(parents=True)
    (paper_dir / "metadata.json").write_text(
        json.dumps({"id": paper_id, "title": "T", "year": 2020, "domain": "other"}),
        encoding="utf-8",
    )
    (paper_dir / "claims.json").write_text("[]", encoding="utf-8")
    llm_out = {
        "paper_id": paper_id,
        "schema_version": "0.1.0",
        "verification_boundary": "human_review_only",
        "proposals": [],
    }
    provider = FakeLLMProvider(reply=json.dumps(llm_out))
    data = generate_llm_claim_proposals(tmp_path, paper_id, provider, model="fake")
    assert data["paper_id"] == paper_id
    assert data["proposals"] == []


def test_preview_apply_claim_proposals_merge_order(tmp_path: Path) -> None:
    paper_id = "p_merge"
    paper_dir = tmp_path / "corpus" / "papers" / paper_id
    paper_dir.mkdir(parents=True)
    existing = [
        {
            "id": f"{paper_id}_claim_a",
            "paper_id": paper_id,
            "section": "1",
            "source_span": {
                "source_file": "s.txt",
                "start": {"page": 1, "offset": 0},
                "end": {"page": 1, "offset": 1},
            },
            "informal_text": "A",
            "claim_type": "theorem",
            "status": "parsed",
            "linked_symbols": [],
            "linked_assumptions": [],
            "linked_formal_targets": [],
        },
        {
            "id": f"{paper_id}_claim_b",
            "paper_id": paper_id,
            "section": "1",
            "source_span": {
                "source_file": "s.txt",
                "start": {"page": 1, "offset": 2},
                "end": {"page": 1, "offset": 3},
            },
            "informal_text": "B",
            "claim_type": "lemma",
            "status": "parsed",
            "linked_symbols": [],
            "linked_assumptions": [],
            "linked_formal_targets": [],
        },
    ]
    (paper_dir / "claims.json").write_text(json.dumps(existing), encoding="utf-8")
    bundle_path = tmp_path / "bundle.json"
    bundle_path.write_text(
        json.dumps(
            {
                "paper_id": paper_id,
                "schema_version": "0.1.0",
                "verification_boundary": "human_review_only",
                "proposals": [
                    {
                        "claim": {
                            "id": f"{paper_id}_claim_new",
                            "paper_id": paper_id,
                            "section": "2",
                            "source_span": {
                                "source_file": "s.txt",
                                "start": {"page": 1, "offset": 10},
                                "end": {"page": 1, "offset": 11},
                            },
                            "informal_text": "N",
                            "claim_type": "definition",
                            "status": "parsed",
                            "linked_symbols": [],
                            "linked_assumptions": [],
                            "linked_formal_targets": [],
                        }
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    before, after = preview_apply_claim_proposals(tmp_path, bundle_path)
    assert [c["id"] for c in before] == [f"{paper_id}_claim_a", f"{paper_id}_claim_b"]
    assert [c["id"] for c in after] == [
        f"{paper_id}_claim_a",
        f"{paper_id}_claim_b",
        f"{paper_id}_claim_new",
    ]


def test_preview_apply_mapping_proposals(tmp_path: Path) -> None:
    paper_id = "p_map"
    paper_dir = tmp_path / "corpus" / "papers" / paper_id
    paper_dir.mkdir(parents=True)
    mapping = {
        "paper_id": paper_id,
        "namespace": "ScientificMemory.Foo",
        "claim_to_decl": {"old": "x"},
    }
    (paper_dir / "mapping.json").write_text(json.dumps(mapping), encoding="utf-8")
    bundle_path = tmp_path / "mb.json"
    bundle_path.write_text(
        json.dumps(
            {
                "paper_id": paper_id,
                "schema_version": "0.1.0",
                "verification_boundary": "human_review_only",
                "proposals": [
                    {"claim_id": "old", "lean_declaration_short_name": "y"},
                    {"claim_id": "new_id", "lean_declaration_short_name": "z"},
                ],
            }
        ),
        encoding="utf-8",
    )
    before, after = preview_apply_mapping_proposals(tmp_path, bundle_path)
    assert before["claim_to_decl"]["old"] == "x"
    assert after["claim_to_decl"]["old"] == "y"
    assert after["claim_to_decl"]["new_id"] == "z"


def test_validate_llm_sidecar_warns_on_invalid(tmp_path: Path) -> None:
    (tmp_path / "schemas").mkdir(parents=True)
    repo_root = Path(__file__).resolve().parents[2]
    import shutil

    for name in (
        "common.schema.json",
        "claim.schema.json",
        "assumption.schema.json",
        "symbol.schema.json",
        "llm_run_provenance.schema.json",
        "llm_claim_proposals.schema.json",
        "llm_mapping_proposals.schema.json",
        "llm_lean_proposals.schema.json",
        "suggested_assumptions.schema.json",
        "suggested_symbols.schema.json",
        "suggested_mapping.schema.json",
    ):
        shutil.copy(repo_root / "schemas" / name, tmp_path / "schemas" / name)
    paper_dir = tmp_path / "corpus" / "papers" / "bad"
    paper_dir.mkdir(parents=True)
    (paper_dir / "llm_claim_proposals.json").write_text('{"not": "valid"}', encoding="utf-8")
    warns = validate_llm_proposal_sidecars_warn(tmp_path)
    assert len(warns) == 1
    assert "llm_claim_proposals.json" in warns[0]
