"""Graph and link integrity tests (Gate 2/3)."""

import json
import tempfile
from pathlib import Path

import pytest

from sm_pipeline.validate.graph import GraphIntegrityError, validate_graph


def _minimal_paper(root: Path, paper_id: str) -> None:
    (root / "corpus" / "papers" / paper_id).mkdir(parents=True)
    (root / "corpus" / "papers" / paper_id / "metadata.json").write_text(
        json.dumps(
            {
                "id": paper_id,
                "title": "T",
                "authors": ["A"],
                "year": 2000,
                "domain": "other",
                "source": {"kind": "pdf", "path": "x", "sha256": "0" * 64},
                "artifact_status": "admitted",
            }
        ),
        encoding="utf-8",
    )
    (root / "corpus" / "papers" / paper_id / "claims.json").write_text(
        json.dumps(
            [
                {
                    "id": "c1",
                    "paper_id": paper_id,
                    "section": "1",
                    "source_span": {
                        "source_file": "x",
                        "start": {"page": 1, "offset": 0},
                        "end": {"page": 1, "offset": 0},
                    },
                    "informal_text": "x",
                    "claim_type": "definition",
                    "status": "unparsed",
                    "value_kind": "foundational_law",
                }
            ]
        ),
        encoding="utf-8",
    )


def test_theorem_card_claim_id_orphan_raises() -> None:
    """Graph check fails when a theorem card references a claim_id not in claims.json."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _minimal_paper(root, "p1")
        (root / "corpus" / "papers" / "p1" / "theorem_cards.json").write_text(
            json.dumps(
                [
                    {
                        "id": "card_1",
                        "claim_id": "nonexistent_claim",
                        "lean_decl": "Foo.bar",
                        "file_path": "",
                        "proof_status": "mapped",
                        "verification_boundary": "human_review_only",
                    }
                ]
            ),
            encoding="utf-8",
        )
        with pytest.raises(GraphIntegrityError, match="claim_id.*does not exist"):
            validate_graph(root)


def test_theorem_card_claim_id_valid_passes() -> None:
    """Graph check passes when every theorem card claim_id exists in claims."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _minimal_paper(root, "p1")
        (root / "corpus" / "papers" / "p1" / "theorem_cards.json").write_text(
            json.dumps(
                [
                    {
                        "id": "card_1",
                        "claim_id": "c1",
                        "lean_decl": "Foo.bar",
                        "file_path": "",
                        "proof_status": "mapped",
                        "verification_boundary": "human_review_only",
                    }
                ]
            ),
            encoding="utf-8",
        )
        validate_graph(root)


def test_mapping_claim_key_orphan_raises() -> None:
    """Graph check fails when mapping.claim_to_decl references a claim not in claims.json."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _minimal_paper(root, "p1")
        (root / "corpus" / "papers" / "p1" / "mapping.json").write_text(
            json.dumps(
                {
                    "paper_id": "p1",
                    "namespace": "Foo",
                    "claim_to_decl": {"nonexistent_claim": "some_decl"},
                }
            ),
            encoding="utf-8",
        )
        with pytest.raises(GraphIntegrityError, match="claim_to_decl key.*does not exist"):
            validate_graph(root)


def test_mapping_claim_key_valid_passes() -> None:
    """Graph check passes when every mapping key exists in claims."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _minimal_paper(root, "p1")
        (root / "corpus" / "papers" / "p1" / "mapping.json").write_text(
            json.dumps(
                {"paper_id": "p1", "namespace": "Foo", "claim_to_decl": {"c1": "some_decl"}}
            ),
            encoding="utf-8",
        )
        validate_graph(root)


def test_dependency_id_orphan_raises() -> None:
    """Graph check fails when a theorem card dependency_id is not a theorem card id in corpus."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _minimal_paper(root, "p1")
        (root / "corpus" / "papers" / "p1" / "theorem_cards.json").write_text(
            json.dumps(
                [
                    {
                        "id": "card_1",
                        "claim_id": "c1",
                        "lean_decl": "Foo.bar",
                        "file_path": "",
                        "proof_status": "mapped",
                        "verification_boundary": "human_review_only",
                        "dependency_ids": ["nonexistent_card_id"],
                    }
                ]
            ),
            encoding="utf-8",
        )
        with pytest.raises(GraphIntegrityError, match="dependency_id.*not a theorem card id"):
            validate_graph(root)


def test_dependency_id_valid_passes() -> None:
    """Graph check passes when dependency_ids reference existing theorem card ids."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "corpus" / "papers" / "p1").mkdir(parents=True)
        (root / "corpus" / "papers" / "p1" / "metadata.json").write_text("{}", encoding="utf-8")
        (root / "corpus" / "papers" / "p1" / "claims.json").write_text(
            json.dumps(
                [
                    {
                        "id": "c1",
                        "paper_id": "p1",
                        "section": "1",
                        "source_span": {
                            "source_file": "x",
                            "start": {"page": 1, "offset": 0},
                            "end": {"page": 1, "offset": 0},
                        },
                        "informal_text": "x",
                        "claim_type": "definition",
                        "status": "unparsed",
                        "value_kind": "foundational_law",
                    },
                    {
                        "id": "c2",
                        "paper_id": "p1",
                        "section": "1",
                        "source_span": {
                            "source_file": "x",
                            "start": {"page": 1, "offset": 0},
                            "end": {"page": 1, "offset": 0},
                        },
                        "informal_text": "y",
                        "claim_type": "theorem",
                        "status": "unparsed",
                        "value_kind": "foundational_law",
                    },
                ]
            ),
            encoding="utf-8",
        )
        (root / "corpus" / "papers" / "p1" / "theorem_cards.json").write_text(
            json.dumps(
                [
                    {
                        "id": "card_1",
                        "claim_id": "c1",
                        "lean_decl": "Foo.def",
                        "file_path": "",
                        "proof_status": "machine_checked",
                        "verification_boundary": "fully_machine_checked",
                        "dependency_ids": [],
                    },
                    {
                        "id": "card_2",
                        "claim_id": "c2",
                        "lean_decl": "Foo.thm",
                        "file_path": "",
                        "proof_status": "machine_checked",
                        "verification_boundary": "fully_machine_checked",
                        "dependency_ids": ["card_1"],
                    },
                ]
            ),
            encoding="utf-8",
        )
        validate_graph(root)


def test_executable_link_orphan_raises_when_kernels_defined() -> None:
    """Graph check fails when a theorem card executable_link is not in kernels.json."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _minimal_paper(root, "p1")
        (root / "corpus" / "papers" / "p1" / "theorem_cards.json").write_text(
            json.dumps(
                [
                    {
                        "id": "card_1",
                        "claim_id": "c1",
                        "lean_decl": "Foo.bar",
                        "file_path": "",
                        "proof_status": "mapped",
                        "verification_boundary": "human_review_only",
                        "executable_links": ["undefined_kernel_id"],
                    }
                ]
            ),
            encoding="utf-8",
        )
        (root / "corpus").mkdir(parents=True, exist_ok=True)
        (root / "corpus" / "kernels.json").write_text(
            json.dumps(
                [
                    {
                        "id": "other_kernel",
                        "domain": "x",
                        "input_schema": "",
                        "output_schema": "",
                        "semantic_contract": "",
                        "linked_theorem_cards": [],
                    }
                ]
            ),
            encoding="utf-8",
        )
        with pytest.raises(GraphIntegrityError, match="executable kernel.*not in corpus/kernels"):
            validate_graph(root)


def test_executable_link_valid_passes_when_kernels_defined() -> None:
    """Graph check passes when executable_links reference kernel ids in kernels.json."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _minimal_paper(root, "p1")
        (root / "corpus" / "papers" / "p1" / "theorem_cards.json").write_text(
            json.dumps(
                [
                    {
                        "id": "card_1",
                        "claim_id": "c1",
                        "lean_decl": "Foo.bar",
                        "file_path": "",
                        "proof_status": "mapped",
                        "verification_boundary": "human_review_only",
                        "executable_links": ["k1"],
                    }
                ]
            ),
            encoding="utf-8",
        )
        (root / "corpus").mkdir(parents=True, exist_ok=True)
        (root / "corpus" / "kernels.json").write_text(
            json.dumps(
                [
                    {
                        "id": "k1",
                        "domain": "x",
                        "io_typing": {
                            "inputs": [{"name": "x", "numeric_kind": "float"}],
                            "outputs": [{"name": "y", "numeric_kind": "float"}],
                        },
                        "semantic_contract": "",
                        "linked_theorem_cards": ["card_1"],
                    }
                ]
            ),
            encoding="utf-8",
        )
        validate_graph(root)


def test_linked_assumption_orphan_raises() -> None:
    """Graph check fails when a claim references an assumption not in assumptions.json."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "corpus" / "papers" / "p1").mkdir(parents=True)
        (root / "corpus" / "papers" / "p1" / "metadata.json").write_text("{}", encoding="utf-8")
        (root / "corpus" / "papers" / "p1" / "claims.json").write_text(
            json.dumps(
                [
                    {
                        "id": "c1",
                        "paper_id": "p1",
                        "section": "1",
                        "source_span": {
                            "source_file": "x",
                            "start": {"page": 1, "offset": 0},
                            "end": {"page": 1, "offset": 0},
                        },
                        "informal_text": "x",
                        "claim_type": "definition",
                        "status": "unparsed",
                        "linked_assumptions": ["nonexistent_assumption"],
                    }
                ]
            ),
            encoding="utf-8",
        )
        (root / "corpus" / "papers" / "p1" / "assumptions.json").write_text(
            json.dumps(
                [
                    {
                        "id": "a1",
                        "paper_id": "p1",
                        "source_span": {
                            "source_file": "x",
                            "start": {"page": 1, "offset": 0},
                            "end": {"page": 1, "offset": 0},
                        },
                        "text": "A",
                        "kind": "domain_restriction",
                    }
                ]
            ),
            encoding="utf-8",
        )
        with pytest.raises(GraphIntegrityError, match="assumption.*does not exist"):
            validate_graph(root)


def test_linked_symbol_orphan_raises() -> None:
    """Graph check fails when a claim references a symbol not in symbols.json."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "corpus" / "papers" / "p1").mkdir(parents=True)
        (root / "corpus" / "papers" / "p1" / "metadata.json").write_text("{}", encoding="utf-8")
        (root / "corpus" / "papers" / "p1" / "claims.json").write_text(
            json.dumps(
                [
                    {
                        "id": "c1",
                        "paper_id": "p1",
                        "section": "1",
                        "source_span": {
                            "source_file": "x",
                            "start": {"page": 1, "offset": 0},
                            "end": {"page": 1, "offset": 0},
                        },
                        "informal_text": "x",
                        "claim_type": "definition",
                        "status": "unparsed",
                        "value_kind": "foundational_law",
                        "linked_symbols": ["nonexistent_symbol"],
                    }
                ]
            ),
            encoding="utf-8",
        )
        (root / "corpus" / "papers" / "p1" / "symbols.json").write_text(
            json.dumps(
                [
                    {
                        "id": "s1",
                        "paper_id": "p1",
                        "raw_latex": "x",
                        "normalized_name": "x",
                        "type_hint": "real",
                    }
                ]
            ),
            encoding="utf-8",
        )
        with pytest.raises(GraphIntegrityError, match="symbol.*does not exist"):
            validate_graph(root)


def test_manifest_kernel_index_orphan_raises() -> None:
    """Graph check fails when manifest.kernel_index references a kernel not in kernels.json."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _minimal_paper(root, "p1")
        (root / "corpus" / "papers" / "p1" / "manifest.json").write_text(
            json.dumps(
                {
                    "paper_id": "p1",
                    "version": "0.1",
                    "build_hash": "0" * 64,
                    "coverage_metrics": {
                        "claim_count": 1,
                        "mapped_claim_count": 0,
                        "machine_checked_count": 0,
                        "kernel_linked_count": 0,
                    },
                    "generated_pages": [],
                    "kernel_index": ["undefined_kernel"],
                }
            ),
            encoding="utf-8",
        )
        (root / "corpus").mkdir(parents=True, exist_ok=True)
        (root / "corpus" / "kernels.json").write_text(
            json.dumps(
                [
                    {
                        "id": "other",
                        "domain": "x",
                        "io_typing": {
                            "inputs": [{"name": "x", "numeric_kind": "float"}],
                            "outputs": [{"name": "y", "numeric_kind": "float"}],
                        },
                        "semantic_contract": "",
                        "linked_theorem_cards": [],
                    }
                ]
            ),
            encoding="utf-8",
        )
        with pytest.raises(GraphIntegrityError, match="kernel_index.*not in corpus/kernels"):
            validate_graph(root)


def test_empty_papers_dir_passes() -> None:
    """Graph check passes when papers dir is empty (no papers to validate)."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "corpus" / "papers").mkdir(parents=True)
        validate_graph(root)
