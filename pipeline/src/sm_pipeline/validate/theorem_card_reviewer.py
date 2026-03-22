"""Theorem card reviewer_status rules (SPEC v0.2)."""

import json
from pathlib import Path

ALLOWED_REVIEWER_STATUS = frozenset({"unreviewed", "reviewed", "blocked", "accepted"})


class TheoremCardReviewerError(Exception):
    pass


def validate_theorem_card_reviewer(repo_root: Path) -> None:
    """
    - reviewer_status is required and must be in allowed enum.
    - reviewer_status blocked requires non-empty notes on the card.
    - reviewer_status accepted requires proof_status machine_checked.
    """
    repo_root = Path(repo_root).resolve()
    papers_dir = repo_root / "corpus" / "papers"
    if not papers_dir.is_dir():
        return

    for paper_dir in sorted(papers_dir.iterdir()):
        if not paper_dir.is_dir():
            continue
        path = paper_dir / "theorem_cards.json"
        if not path.exists():
            continue
        try:
            cards = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        if not isinstance(cards, list):
            continue
        for c in cards:
            if not isinstance(c, dict):
                continue
            rs = c.get("reviewer_status")
            if rs is None:
                raise TheoremCardReviewerError(
                    f"Paper {paper_dir.name} card {c.get('id')}: reviewer_status is required"
                )
            if str(rs) not in ALLOWED_REVIEWER_STATUS:
                raise TheoremCardReviewerError(
                    f"Paper {paper_dir.name} card {c.get('id')}: invalid reviewer_status {rs!r}"
                )
            if str(rs or "") == "blocked":
                notes = (c.get("notes") or "").strip()
                if not notes:
                    raise TheoremCardReviewerError(
                        f"Paper {paper_dir.name} card {c.get('id')}: "
                        "reviewer_status blocked "
                        "requires non-empty notes"
                    )
            if str(rs) == "accepted":
                proof_status = str(c.get("proof_status") or "")
                if proof_status != "machine_checked":
                    raise TheoremCardReviewerError(
                        f"Paper {paper_dir.name} card {c.get('id')}: "
                        "reviewer_status accepted "
                        "requires proof_status machine_checked"
                    )
