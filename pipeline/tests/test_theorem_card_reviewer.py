"""Theorem-card reviewer_status validation tests."""

import json
import tempfile
from pathlib import Path

import pytest

from sm_pipeline.validate.theorem_card_reviewer import (
    TheoremCardReviewerError,
    validate_theorem_card_reviewer,
)


def _write_cards(root: Path, cards: list[dict]) -> None:
    paper_dir = root / "corpus" / "papers" / "p1"
    paper_dir.mkdir(parents=True)
    (paper_dir / "theorem_cards.json").write_text(
        json.dumps(cards),
        encoding="utf-8",
    )


def test_missing_reviewer_status_raises() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _write_cards(
            root,
            [
                {
                    "id": "c1",
                    "claim_id": "q1",
                    "lean_decl": "N.x",
                    "file_path": "formal/F.lean",
                    "proof_status": "machine_checked",
                    "verification_boundary": "fully_machine_checked",
                }
            ],
        )
        with pytest.raises(TheoremCardReviewerError, match="reviewer_status is required"):
            validate_theorem_card_reviewer(root)


def test_blocked_requires_notes() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _write_cards(
            root,
            [
                {
                    "id": "c1",
                    "claim_id": "q1",
                    "lean_decl": "N.x",
                    "file_path": "formal/F.lean",
                    "proof_status": "mapped",
                    "verification_boundary": "human_review_only",
                    "reviewer_status": "blocked",
                }
            ],
        )
        with pytest.raises(TheoremCardReviewerError, match="requires non-empty notes"):
            validate_theorem_card_reviewer(root)


def test_accepted_requires_machine_checked() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _write_cards(
            root,
            [
                {
                    "id": "c1",
                    "claim_id": "q1",
                    "lean_decl": "N.x",
                    "file_path": "formal/F.lean",
                    "proof_status": "linked_to_kernel",
                    "verification_boundary": "numerically_witnessed",
                    "reviewer_status": "accepted",
                }
            ],
        )
        with pytest.raises(TheoremCardReviewerError, match="requires proof_status machine_checked"):
            validate_theorem_card_reviewer(root)


def test_valid_reviewer_card_passes() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _write_cards(
            root,
            [
                {
                    "id": "c1",
                    "claim_id": "q1",
                    "lean_decl": "N.x",
                    "file_path": "formal/F.lean",
                    "proof_status": "machine_checked",
                    "verification_boundary": "fully_machine_checked",
                    "reviewer_status": "accepted",
                }
            ],
        )
        validate_theorem_card_reviewer(root)
