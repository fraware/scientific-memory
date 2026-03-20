"""Coverage integrity tests (Gate 4)."""

import json
import tempfile
from pathlib import Path

import pytest

from sm_pipeline.validate.coverage import CoverageIntegrityError, validate_coverage


def test_manifest_wrong_claim_count_raises() -> None:
    """Coverage check fails when manifest.claim_count does not match claims.json length."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "corpus" / "papers" / "p1").mkdir(parents=True)
        (root / "corpus" / "papers" / "p1" / "claims.json").write_text(
            json.dumps([{"id": "c1", "paper_id": "p1"}]),
            encoding="utf-8",
        )
        (root / "corpus" / "papers" / "p1" / "manifest.json").write_text(
            json.dumps(
                {
                    "paper_id": "p1",
                    "version": "0.1",
                    "build_hash": "0" * 64,
                    "coverage_metrics": {
                        "claim_count": 99,
                        "mapped_claim_count": 0,
                        "machine_checked_count": 0,
                        "kernel_linked_count": 0,
                    },
                    "generated_pages": [],
                }
            ),
            encoding="utf-8",
        )
        with pytest.raises(CoverageIntegrityError, match="claim_count"):
            validate_coverage(root)


def test_manifest_matching_counts_passes() -> None:
    """Coverage check passes when manifest.coverage_metrics matches claims-derived counts."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "corpus" / "papers" / "p1").mkdir(parents=True)
        claims = [
            {
                "id": "c1",
                "paper_id": "p1",
                "section": "1",
                "informal_text": "x",
                "claim_type": "definition",
                "status": "unparsed",
            },
            {
                "id": "c2",
                "paper_id": "p1",
                "section": "1",
                "informal_text": "y",
                "claim_type": "theorem",
                "status": "machine_checked",
                "linked_formal_targets": ["Decl"],
            },
        ]
        (root / "corpus" / "papers" / "p1" / "claims.json").write_text(
            json.dumps(claims),
            encoding="utf-8",
        )
        (root / "corpus" / "papers" / "p1" / "manifest.json").write_text(
            json.dumps(
                {
                    "paper_id": "p1",
                    "version": "0.1",
                    "build_hash": "0" * 64,
                    "coverage_metrics": {
                        "claim_count": 2,
                        "mapped_claim_count": 1,
                        "machine_checked_count": 1,
                        "kernel_linked_count": 0,
                    },
                    "generated_pages": [],
                }
            ),
            encoding="utf-8",
        )
        validate_coverage(root)


def test_manifest_coverage_counts() -> None:
    """Manifest coverage counts match corpus (sanity on real structure)."""
    from sm_pipeline.validate.coverage import validate_coverage as run

    repo_root = Path(__file__).resolve().parents[2]
    papers_dir = repo_root / "corpus" / "papers"
    if not papers_dir.is_dir():
        pytest.skip("no corpus")
    run(repo_root)
