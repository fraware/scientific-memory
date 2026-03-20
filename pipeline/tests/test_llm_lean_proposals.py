"""LLM Lean proposal generation, converter, and sidecar validation (no live API by default)."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from sm_pipeline.llm.lean_proposal_to_apply import lean_proposal_to_apply_bundle_dict
from sm_pipeline.llm.proposals_lean import generate_llm_lean_proposals
from sm_pipeline.llm.provider import FakeLLMProvider
from sm_pipeline.validate.llm_proposals import validate_llm_proposal_sidecars_warn


def test_generate_llm_lean_proposals_fake(tmp_path: Path) -> None:
    paper_id = "p_lean_test"
    paper_dir = tmp_path / "corpus" / "papers" / paper_id
    paper_dir.mkdir(parents=True)
    (paper_dir / "mapping.json").write_text(
        json.dumps(
            {
                "paper_id": paper_id,
                "namespace": "ScientificMemory.Mathematics.SumEvens",
                "claim_to_decl": {"c1": "sum_evens"},
                "target_file": "formal/ScientificMemory/Mathematics/SumEvens.lean",
            }
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
                    "claim_type": "theorem",
                    "status": "mapped",
                    "source_span": {
                        "source_file": "s.pdf",
                        "start": {"page": 1, "offset": 0},
                        "end": {"page": 1, "offset": 1},
                    },
                }
            ]
        ),
        encoding="utf-8",
    )
    formal = tmp_path / "formal" / "ScientificMemory" / "Mathematics"
    formal.mkdir(parents=True)
    (formal / "SumEvens.lean").write_text("theorem t : True := by sorry\n", encoding="utf-8")

    llm_out = {
        "paper_id": paper_id,
        "schema_version": "0.1.0",
        "verification_boundary": "human_review_only",
        "proposals": [
            {
                "proposal_id": "p1",
                "paper_id": paper_id,
                "claim_id": "c1",
                "target_file": "formal/ScientificMemory/Mathematics/SumEvens.lean",
                "target_decl": "t",
                "edit_kind": "proof_repair",
                "replacements": [{"find": "sorry", "replace": "exact True.intro"}],
                "rationale": "x",
                "confidence": 0.5,
            }
        ],
    }
    provider = FakeLLMProvider(reply=json.dumps(llm_out))
    data = generate_llm_lean_proposals(tmp_path, paper_id, provider, model="fake")
    assert data["paper_id"] == paper_id
    assert len(data["proposals"]) == 1
    assert data["proposals"][0]["proposal_id"] == "p1"


def test_generate_llm_lean_proposals_normalizes_edit_kind_alias(tmp_path: Path) -> None:
    paper_id = "p_lean_alias"
    paper_dir = tmp_path / "corpus" / "papers" / paper_id
    paper_dir.mkdir(parents=True)
    (paper_dir / "mapping.json").write_text(
        json.dumps(
            {
                "paper_id": paper_id,
                "namespace": "ScientificMemory.Mathematics.SumEvens",
                "claim_to_decl": {"c1": "sum_evens"},
                "target_file": "formal/ScientificMemory/Mathematics/SumEvens.lean",
            }
        ),
        encoding="utf-8",
    )
    (paper_dir / "claims.json").write_text("[]", encoding="utf-8")
    formal = tmp_path / "formal" / "ScientificMemory" / "Mathematics"
    formal.mkdir(parents=True)
    (formal / "SumEvens.lean").write_text("theorem t : True := by sorry\n", encoding="utf-8")

    llm_out = {
        "paper_id": paper_id,
        "schema_version": "0.1.0",
        "verification_boundary": "human_review_only",
        "proposals": [
            {
                "proposal_id": "p1",
                "paper_id": paper_id,
                "target_file": "formal/ScientificMemory/Mathematics/SumEvens.lean",
                "edit_kind": "proof_improvement",
                "replacements": [{"find": "sorry", "replace": "exact True.intro"}],
            }
        ],
    }
    provider = FakeLLMProvider(reply=json.dumps(llm_out))
    data = generate_llm_lean_proposals(tmp_path, paper_id, provider, model="fake")
    assert data["proposals"][0]["edit_kind"] == "proof_repair"


def test_lean_proposal_to_apply_bundle_dict_ok() -> None:
    bundle = {
        "paper_id": "p",
        "schema_version": "0.1.0",
        "verification_boundary": "human_review_only",
        "proposals": [
            {
                "proposal_id": "x",
                "paper_id": "p",
                "target_file": "formal/Foo.lean",
                "edit_kind": "proof_repair",
                "replacements": [{"find": "a", "replace": "b"}],
            }
        ],
    }
    apply_b = lean_proposal_to_apply_bundle_dict(bundle, proposal_id="x")
    assert apply_b["verification_boundary"] == "human_review_only"
    assert len(apply_b["patches"]) == 1
    assert apply_b["patches"][0]["relative_path"] == "formal/Foo.lean"
    assert apply_b["patches"][0]["replacements"][0]["find"] == "a"


def test_lean_proposal_to_apply_bundle_dict_no_replacements_raises() -> None:
    bundle = {
        "paper_id": "p",
        "schema_version": "0.1.0",
        "verification_boundary": "human_review_only",
        "proposals": [
            {
                "proposal_id": "x",
                "paper_id": "p",
                "target_file": "formal/Foo.lean",
                "edit_kind": "new_theorem",
                "replacements": [],
            }
        ],
    }
    with pytest.raises(ValueError, match="empty replacements"):
        lean_proposal_to_apply_bundle_dict(bundle, proposal_id="x")


def test_validate_llm_lean_sidecar_invalid_warns(tmp_path: Path) -> None:
    repo = Path(__file__).resolve().parents[2]
    shutil.copytree(repo / "schemas", tmp_path / "schemas")
    paper_dir = tmp_path / "corpus" / "papers" / "lean_bad"
    paper_dir.mkdir(parents=True)
    (paper_dir / "llm_lean_proposals.json").write_text('{"paper_id": "x"}', encoding="utf-8")
    warns = validate_llm_proposal_sidecars_warn(tmp_path)
    assert warns
    assert any("llm_lean_proposals.json" in w for w in warns)
