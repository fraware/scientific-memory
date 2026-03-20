"""Unit tests for build_hash v2 and publish manifest graph recompute (trust hardening)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from sm_pipeline.publish import manifest as manifest_mod
from sm_pipeline.publish.manifest import publish_manifest


def _minimal_claim(paper_id: str, cid: str = "c1") -> dict:
    return {
        "id": cid,
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


def test_compute_build_hash_v2_changes_when_claims_change(tmp_path: Path) -> None:
    paper_id = "hash_v2_paper"
    paper_dir = tmp_path / "corpus" / "papers" / paper_id
    paper_dir.mkdir(parents=True)
    cards = [{"id": f"{paper_id}_card_001", "claim_id": "c1", "lean_decl": "N.T"}]
    ki = ["k1"]
    decl_idx = ["N.T"]

    (paper_dir / "claims.json").write_text(
        json.dumps([_minimal_claim(paper_id)]), encoding="utf-8"
    )
    (paper_dir / "assumptions.json").write_text("[]", encoding="utf-8")
    (paper_dir / "symbols.json").write_text("[]", encoding="utf-8")
    (paper_dir / "mapping.json").write_text(
        json.dumps({"namespace": "N", "claim_to_decl": {"c1": "T"}}), encoding="utf-8"
    )

    h1, v1 = manifest_mod._compute_build_hash(paper_dir, paper_id, decl_idx, cards, ki)
    assert v1 == "2"
    (paper_dir / "claims.json").write_text(
        json.dumps([{**_minimal_claim(paper_id), "informal_text": "changed"}]), encoding="utf-8"
    )
    h2, v2 = manifest_mod._compute_build_hash(paper_dir, paper_id, decl_idx, cards, ki)
    assert v2 == "2"
    assert h1 != h2


def test_compute_build_hash_v2_deterministic_same_inputs(tmp_path: Path) -> None:
    paper_id = "hash_v2_det"
    paper_dir = tmp_path / "corpus" / "papers" / paper_id
    paper_dir.mkdir(parents=True)
    (paper_dir / "claims.json").write_text(
        json.dumps([_minimal_claim(paper_id)]), encoding="utf-8"
    )
    (paper_dir / "assumptions.json").write_text("[]", encoding="utf-8")
    (paper_dir / "symbols.json").write_text("[]", encoding="utf-8")
    (paper_dir / "mapping.json").write_text("{}", encoding="utf-8")
    cards_key_order_a = [{"id": "c1", "z": 1}]
    cards_key_order_b = [{"z": 1, "id": "c1"}]
    ki = ["b", "a"]
    decl_idx = ["d2", "d1"]
    h1, _ = manifest_mod._compute_build_hash(
        paper_dir, paper_id, decl_idx, cards_key_order_a, ki
    )
    h2, _ = manifest_mod._compute_build_hash(
        paper_dir, paper_id, decl_idx, cards_key_order_b, ki
    )
    assert h1 == h2


def test_compute_build_hash_legacy_when_claims_missing(tmp_path: Path) -> None:
    paper_id = "hash_legacy"
    paper_dir = tmp_path / "corpus" / "papers" / paper_id
    paper_dir.mkdir(parents=True)
    cards = [{"id": "x", "file_path": "f.lean"}]
    h, ver = manifest_mod._compute_build_hash(paper_dir, paper_id, ["D"], cards, [])
    assert ver == "1"
    assert len(h) == 64


def test_publish_recomputes_stale_dependency_graph(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    paper_id = "pub_graph_fresh"
    paper_dir = tmp_path / "corpus" / "papers" / paper_id
    paper_dir.mkdir(parents=True)
    (paper_dir / "claims.json").write_text(
        json.dumps([_minimal_claim(paper_id)]), encoding="utf-8"
    )
    (paper_dir / "mapping.json").write_text(
        json.dumps({"namespace": "TestNs", "claim_to_decl": {"c1": "Thm1"}}),
        encoding="utf-8",
    )
    stale_manifest = {
        "paper_id": paper_id,
        "dependency_graph": [{"from": "stale_from", "to": "stale_to"}],
        "kernel_index": ["stale_kernel"],
        "declaration_index": [],
    }
    (paper_dir / "manifest.json").write_text(json.dumps(stale_manifest), encoding="utf-8")

    monkeypatch.delenv("SM_PUBLISH_REUSE_MANIFEST_GRAPHS", raising=False)
    publish_manifest(tmp_path, paper_id)
    out = json.loads((paper_dir / "manifest.json").read_text(encoding="utf-8"))
    assert out["dependency_graph"] == []
    assert out["kernel_index"] == []


def test_publish_reuse_manifest_graphs_env_preserves_stale_graph(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    paper_id = "pub_graph_reuse"
    paper_dir = tmp_path / "corpus" / "papers" / paper_id
    paper_dir.mkdir(parents=True)
    (paper_dir / "claims.json").write_text(
        json.dumps([_minimal_claim(paper_id)]), encoding="utf-8"
    )
    (paper_dir / "mapping.json").write_text(
        json.dumps({"namespace": "TestNs", "claim_to_decl": {"c1": "Thm1"}}),
        encoding="utf-8",
    )
    stale = [{"from": "keep_from", "to": "keep_to"}]
    stale_ki = ["kept_kernel"]
    (paper_dir / "manifest.json").write_text(
        json.dumps(
            {
                "paper_id": paper_id,
                "dependency_graph": stale,
                "kernel_index": stale_ki,
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("SM_PUBLISH_REUSE_MANIFEST_GRAPHS", "1")
    try:
        publish_manifest(tmp_path, paper_id)
    finally:
        monkeypatch.delenv("SM_PUBLISH_REUSE_MANIFEST_GRAPHS", raising=False)
    out = json.loads((paper_dir / "manifest.json").read_text(encoding="utf-8"))
    assert out["dependency_graph"] == stale
    assert out["kernel_index"] == stale_ki


def test_double_publish_identical_build_hash(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Consecutive publishes with no source edits yield the same build_hash (determinism)."""
    monkeypatch.delenv("SM_PUBLISH_REUSE_MANIFEST_GRAPHS", raising=False)
    paper_id = "pub_det_repeat"
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
    h1 = json.loads((paper_dir / "manifest.json").read_text(encoding="utf-8"))["build_hash"]
    publish_manifest(tmp_path, paper_id)
    h2 = json.loads((paper_dir / "manifest.json").read_text(encoding="utf-8"))["build_hash"]
    assert h1 == h2
    assert json.loads((paper_dir / "manifest.json").read_text(encoding="utf-8"))[
        "build_hash_version"
    ] == "2"


def test_compute_build_hash_v2_kernel_index_affects_hash(tmp_path: Path) -> None:
    paper_id = "hash_ki"
    paper_dir = tmp_path / "corpus" / "papers" / paper_id
    paper_dir.mkdir(parents=True)
    (paper_dir / "claims.json").write_text(
        json.dumps([_minimal_claim(paper_id)]), encoding="utf-8"
    )
    (paper_dir / "assumptions.json").write_text("[]", encoding="utf-8")
    (paper_dir / "symbols.json").write_text("[]", encoding="utf-8")
    (paper_dir / "mapping.json").write_text("{}", encoding="utf-8")
    cards = [{"id": "c"}]
    h1, _ = manifest_mod._compute_build_hash(paper_dir, paper_id, ["d"], cards, ["k1"])
    h2, _ = manifest_mod._compute_build_hash(paper_dir, paper_id, ["d"], cards, ["k2"])
    assert h1 != h2
