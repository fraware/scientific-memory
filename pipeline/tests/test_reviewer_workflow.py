"""Reviewer workflow validation tests."""

import json
import tempfile
from pathlib import Path

import pytest

from sm_pipeline.validate.reviewer import (
    ReviewerWorkflowError,
    compute_reviewer_report,
    validate_reviewer_lifecycle,
    validate_reviewer_workflow,
)


def test_disputed_claim_without_review_notes_raises() -> None:
    """Validation fails when a claim has status disputed but no review_notes."""
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
                        "informal_text": "Claim.",
                        "claim_type": "theorem",
                        "status": "disputed",
                        "value_kind": "foundational_law",
                    }
                ]
            ),
            encoding="utf-8",
        )
        with pytest.raises(ReviewerWorkflowError, match="disputed.*no review_notes"):
            validate_reviewer_workflow(root)


def test_disputed_claim_with_review_notes_passes() -> None:
    """Validation passes when disputed claim has review_notes."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "corpus" / "papers" / "p1").mkdir(parents=True)
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
                        "informal_text": "Claim.",
                        "claim_type": "theorem",
                        "status": "disputed",
                        "review_notes": "Formalization revealed missing hypothesis.",
                        "value_kind": "foundational_law",
                    }
                ]
            ),
            encoding="utf-8",
        )
        validate_reviewer_workflow(root)


def test_non_disputed_claim_without_notes_passes() -> None:
    """Validation passes when claim is not disputed (review_notes optional)."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "corpus" / "papers" / "p1").mkdir(parents=True)
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
                        "informal_text": "Claim.",
                        "claim_type": "theorem",
                        "status": "machine_checked",
                    }
                ]
            ),
            encoding="utf-8",
        )
        validate_reviewer_workflow(root)


def test_invalid_status_raises_lifecycle() -> None:
    """validate_reviewer_lifecycle rejects claim with invalid status."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "corpus" / "papers" / "p1").mkdir(parents=True)
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
                        "informal_text": "Claim.",
                        "claim_type": "theorem",
                        "status": "invalid_status_value",
                        "value_kind": "foundational_law",
                    }
                ]
            ),
            encoding="utf-8",
        )
        with pytest.raises(ReviewerWorkflowError, match="invalid status"):
            validate_reviewer_lifecycle(root)


def test_compute_reviewer_report_includes_claims_by_status() -> None:
    """compute_reviewer_report returns claims_by_status and disputed lists."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "corpus" / "papers" / "p1").mkdir(parents=True)
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
                        "informal_text": "Claim.",
                        "claim_type": "theorem",
                        "status": "machine_checked",
                        "value_kind": "foundational_law",
                    }
                ]
            ),
            encoding="utf-8",
        )
        report = compute_reviewer_report(root)
        assert "machine_checked" in report["claims_by_status"]
        assert report["claims_by_status"]["machine_checked"][0]["claim_id"] == "c1"
        assert report["invalid_status_claims"] == []
