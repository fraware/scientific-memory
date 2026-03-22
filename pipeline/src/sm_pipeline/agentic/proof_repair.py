"""
Proof-repair / agentic assistance interface with explicit verification boundaries.

All outputs from this module are labeled verification_boundary="human_review_only":
they must not be applied to the corpus without human review. This interface is the
contract for future agentic proof-repair or suggestion tools (v0.3).
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

VALID_BOUNDARIES = (
    "fully_machine_checked",
    "machine_checked_plus_axioms",
    "numerically_witnessed",
    "schema_valid_only",
    "human_review_only",
)

INTERFACE_BOUNDARY = "human_review_only"


def suggest_verification_boundary(theorem_card: dict) -> dict:
    """
    Suggest a verification boundary for a theorem card (stub for agentic integration).

    Input: theorem_card dict with at least proof_status, verification_boundary, lean_decl.
    Output: dict with
      - suggested_boundary: str (from VALID_BOUNDARIES)
      - interface_verification_boundary: "human_review_only" (this interface is not trusted)
      - repair_hints: list[str] (optional; empty in stub)

    All callers must treat the result as human_review_only and not auto-apply to corpus.
    """
    current = (theorem_card.get("verification_boundary") or "").strip()
    if current in VALID_BOUNDARIES:
        suggested = current
    else:
        suggested = "human_review_only"
    return {
        "suggested_boundary": suggested,
        "interface_verification_boundary": INTERFACE_BOUNDARY,
        "repair_hints": [],
    }


def _needs_repair_proposal(card: dict) -> bool:
    """True if card is not fully machine-checked (candidate for repair proposal)."""
    status = (card.get("proof_status") or "").strip()
    boundary = (card.get("verification_boundary") or "").strip()
    if status == "machine_checked" and boundary == "fully_machine_checked":
        return False
    return True


def _suggested_action(card: dict) -> str:
    """Deterministic suggested action label for a theorem card."""
    status = (card.get("proof_status") or "").strip()
    boundary = (card.get("verification_boundary") or "").strip()
    if status in ("stubbed", "compiles_with_sorries"):
        return "consider_completing_proof"
    if boundary == "human_review_only":
        return "consider_machine_verification"
    if boundary == "machine_checked_plus_axioms":
        return "consider_axiom_reduction"
    if status != "machine_checked":
        return "consider_completing_proof"
    return "consider_review"


def generate_repair_proposals(repo_root: Path, paper_id: str | None = None) -> dict:
    """
    Build a list of proof-repair proposals from theorem cards. Only cards that are
    not fully_machine_checked (or not fully_machine_checked boundary) get a proposal.
    Returns a dict conforming to proof_repair_proposal.schema.json; never modifies corpus.
    """
    repo_root = Path(repo_root).resolve()
    papers_dir = repo_root / "corpus" / "papers"
    proposals: list[dict] = []
    if not papers_dir.is_dir():
        return _wrap_proposals(proposals, paper_id)

    for paper_dir in sorted(papers_dir.iterdir()):
        if not paper_dir.is_dir():
            continue
        pid = paper_dir.name
        if paper_id is not None and pid != paper_id:
            continue
        cards_path = paper_dir / "theorem_cards.json"
        if not cards_path.exists():
            continue
        try:
            data = json.loads(cards_path.read_text(encoding="utf-8"))
            cards = data if isinstance(data, list) else []
        except (json.JSONDecodeError, OSError):
            cards = []
        for card in cards:
            if not isinstance(card, dict):
                continue
            if not _needs_repair_proposal(card):
                continue
            proposals.append(
                {
                    "theorem_card_id": str(card.get("id", "")),
                    "paper_id": pid,
                    "claim_id": str(card.get("claim_id", "")),
                    "lean_decl": str(card.get("lean_decl", "")),
                    "file_path": str(card.get("file_path", "")),
                    "current_proof_status": str(card.get("proof_status", "")),
                    "current_verification_boundary": str(card.get("verification_boundary", "")),
                    "suggested_action": _suggested_action(card),
                    "repair_hints": [],
                }
            )

    return _wrap_proposals(proposals, paper_id)


def _wrap_proposals(proposals: list[dict], paper_id: str | None) -> dict:
    out: dict = {
        "verification_boundary": INTERFACE_BOUNDARY,
        "proposals": proposals,
        "generated_at": datetime.now(UTC).isoformat(),
    }
    if paper_id:
        out["paper_id"] = paper_id
    return out
