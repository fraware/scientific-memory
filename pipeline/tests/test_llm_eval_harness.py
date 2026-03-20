"""LLM eval fixtures, prompt provenance, and llm_eval benchmark scorer (offline)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from sm_pipeline.benchmark_runner import run_benchmarks
from sm_pipeline.llm.prompt_templates import (
    CLAIM_PROMPT_TEMPLATE_ID,
    declared_llm_prompt_template_versions,
    sha256_hex,
)
from sm_pipeline.llm.proposals_claims import generate_llm_claim_proposals
from sm_pipeline.llm.provider import FakeLLMProvider


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def test_declared_llm_prompt_template_versions_shape() -> None:
    d = declared_llm_prompt_template_versions()
    assert len(d) == 3
    for _tid, h in d.items():
        assert len(h) == 64
        assert all(c in "0123456789abcdef" for c in h)


def test_run_benchmarks_includes_llm_prompt_templates() -> None:
    report = run_benchmarks(_repo_root())
    pt = report.get("llm_prompt_templates")
    assert isinstance(pt, dict)
    assert CLAIM_PROMPT_TEMPLATE_ID in pt
    assert len(pt[CLAIM_PROMPT_TEMPLATE_ID]) == 64


def test_run_benchmarks_includes_llm_eval_task() -> None:
    report = run_benchmarks(_repo_root())
    task = report["tasks"].get("llm_eval")
    assert isinstance(task, dict)
    assert "error" not in task
    for key in (
        "cases_scanned",
        "gold_claim_id_recall_micro",
        "mapping_keys_recall_micro",
        "lean_reference_conversion_ready",
    ):
        assert key in task
    assert task["cases_scanned"] >= 1
    assert task["gold_claim_id_recall_micro"] == pytest.approx(1.0)
    assert task["mapping_keys_recall_micro"] == pytest.approx(1.0)
    assert task["lean_reference_conversion_ready"] >= 1


def test_generate_llm_claim_proposals_metadata_includes_template_digest(
    tmp_path: Path,
) -> None:
    paper_id = "p_meta"
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
    meta = data.get("metadata") or {}
    assert meta.get("prompt_template_id") == CLAIM_PROMPT_TEMPLATE_ID
    assert meta.get("prompt_template_sha256") == declared_llm_prompt_template_versions()[
        CLAIM_PROMPT_TEMPLATE_ID
    ]
    dig = meta.get("input_artifact_sha256")
    assert isinstance(dig, dict)
    assert "metadata_json" in dig
    assert len(dig["metadata_json"]) == 64
    assert dig["metadata_json"] == sha256_hex(
        json.dumps(json.loads((paper_dir / "metadata.json").read_text(encoding="utf-8")), indent=2)
    )
