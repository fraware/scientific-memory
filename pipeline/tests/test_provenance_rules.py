"""Provenance rules tests (Gate 3)."""

import json
import tempfile
from pathlib import Path

import pytest

from sm_pipeline.validate.provenance import (
    ProvenanceError,
    validate_provenance,
)


def test_claim_without_source_span_raises() -> None:
    """Provenance check fails when a claim lacks source_span."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "corpus" / "papers" / "p1").mkdir(parents=True)
        (root / "corpus" / "papers" / "p1" / "metadata.json").write_text(
            json.dumps(
                {
                    "id": "p1",
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
        (root / "corpus" / "papers" / "p1" / "claims.json").write_text(
            json.dumps(
                [
                    {
                        "id": "c1",
                        "paper_id": "p1",
                        "section": "1",
                        "informal_text": "x",
                        "claim_type": "definition",
                        "status": "unparsed",
                    }
                ]
            ),
            encoding="utf-8",
        )
        with pytest.raises(ProvenanceError, match="missing source_span"):
            validate_provenance(root)


def test_claim_with_source_span_passes() -> None:
    """Provenance check passes when all claims have source_span."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "corpus" / "papers" / "p1").mkdir(parents=True)
        (root / "corpus" / "papers" / "p1" / "metadata.json").write_text(
            json.dumps(
                {
                    "id": "p1",
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
                    }
                ]
            ),
            encoding="utf-8",
        )
        validate_provenance(root)


def test_dangling_declaration_raises() -> None:
    """Provenance fails when declaration_index has an unmapped declaration."""
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
                    }
                ]
            ),
            encoding="utf-8",
        )
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
                    "declaration_index": ["Some.Namespace.orphan_decl"],
                }
            ),
            encoding="utf-8",
        )
        (root / "corpus" / "papers" / "p1" / "mapping.json").write_text(
            json.dumps(
                {
                    "paper_id": "p1",
                    "namespace": "Some.Namespace",
                    "claim_to_decl": {},
                }
            ),
            encoding="utf-8",
        )
        with pytest.raises(ProvenanceError, match="no originating claim"):
            validate_provenance(root)


def test_manifest_with_zero_sha_raises_for_non_stress_paper() -> None:
    """Manifest + sentinel source hash is rejected for normal papers."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "corpus" / "papers" / "p1").mkdir(parents=True)
        (root / "corpus" / "papers" / "p1" / "metadata.json").write_text(
            json.dumps(
                {
                    "id": "p1",
                    "title": "T",
                    "authors": ["A"],
                    "year": 2000,
                    "domain": "other",
                    "source": {"kind": "pdf", "path": "x", "sha256": "0" * 64},
                    "artifact_status": "admitted",
                    "tags": ["domain:test"],
                }
            ),
            encoding="utf-8",
        )
        (root / "corpus" / "papers" / "p1" / "claims.json").write_text("[]", encoding="utf-8")
        (root / "corpus" / "papers" / "p1" / "manifest.json").write_text(
            json.dumps(
                {
                    "paper_id": "p1",
                    "version": "0.1.0",
                    "build_hash": "0" * 64,
                    "coverage_metrics": {
                        "claim_count": 0,
                        "mapped_claim_count": 0,
                        "machine_checked_count": 0,
                        "kernel_linked_count": 0,
                    },
                    "generated_pages": [],
                }
            ),
            encoding="utf-8",
        )
        with pytest.raises(ProvenanceError, match="all-zero sentinel"):
            validate_provenance(root)


def test_manifest_with_zero_sha_allowed_for_hardness_scaffold() -> None:
    """Manifest + sentinel source hash is allowed for empty hard scaffolds."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "corpus" / "papers" / "p1").mkdir(parents=True)
        (root / "corpus" / "papers" / "p1" / "metadata.json").write_text(
            json.dumps(
                {
                    "id": "p1",
                    "title": "T",
                    "authors": ["A"],
                    "year": 2000,
                    "domain": "other",
                    "source": {"kind": "pdf", "path": "x", "sha256": "0" * 64},
                    "artifact_status": "admitted",
                    "tags": ["hardness.primary:units_and_dimensional_analysis"],
                }
            ),
            encoding="utf-8",
        )
        (root / "corpus" / "papers" / "p1" / "claims.json").write_text("[]", encoding="utf-8")
        (root / "corpus" / "papers" / "p1" / "manifest.json").write_text(
            json.dumps(
                {
                    "paper_id": "p1",
                    "version": "0.1.0",
                    "build_hash": "0" * 64,
                    "coverage_metrics": {
                        "claim_count": 0,
                        "mapped_claim_count": 0,
                        "machine_checked_count": 0,
                        "kernel_linked_count": 0,
                    },
                    "generated_pages": [],
                }
            ),
            encoding="utf-8",
        )
        validate_provenance(root)
