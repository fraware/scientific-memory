"""Derive theorem cards from mapping + claims (Path 1: pipeline-only)."""

import json
from pathlib import Path


def _target_file_from_mapping(mapping: dict) -> str:
    """Resolve Lean target file path from mapping (explicit target_file or inferred from namespace)."""
    explicit = (mapping.get("target_file") or "").strip()
    if explicit:
        return explicit
    namespace = (mapping.get("namespace") or "").strip()
    if not namespace:
        return ""
    # Infer path: ScientificMemory.Chemistry.Adsorption.Langmuir1918 -> formal/ScientificMemory/Chemistry/Adsorption/Langmuir1918.lean
    path_part = namespace.replace(".", "/")
    return f"formal/{path_part}.lean"


def derive_theorem_cards(paper_dir: Path, paper_id: str) -> list[dict]:
    """
    Build theorem card records from mapping.claim_to_decl and claims.
    One card per (claim_id, declaration) with proof_status from claim.status.
    file_path is set from mapping.target_file or inferred from mapping.namespace.
    """
    mapping_path = paper_dir / "mapping.json"
    claims_path = paper_dir / "claims.json"
    if not mapping_path.exists() or not claims_path.exists():
        return []
    mapping = json.loads(mapping_path.read_text(encoding="utf-8"))
    claims = json.loads(claims_path.read_text(encoding="utf-8"))
    if not isinstance(mapping, dict) or not isinstance(claims, list):
        return []
    namespace = (mapping.get("namespace") or "").strip()
    claim_to_decl = mapping.get("claim_to_decl") or {}
    if not isinstance(claim_to_decl, dict):
        return []

    file_path = _target_file_from_mapping(mapping)
    claims_by_id = {str(c.get("id")): c for c in claims if isinstance(c, dict) and c.get("id")}
    cards = []
    for idx, (claim_id, short_decl) in enumerate(claim_to_decl.items(), start=1):
        lean_decl = f"{namespace}.{short_decl}" if namespace else short_decl
        claim = claims_by_id.get(claim_id)
        proof_status = claim.get("status", "mapped") if claim else "mapped"
        verification_boundary = _status_to_boundary(proof_status)
        card_id = (
            f"{paper_id}_card_{idx:03d}"
            if len(claim_to_decl) > 1
            else f"{paper_id.replace('-', '_')}_card_001"
        )
        reviewer_status = (
            "accepted"
            if proof_status == "machine_checked"
            else "reviewed"
            if proof_status == "linked_to_kernel"
            else "unreviewed"
        )
        cards.append(
            {
                "id": card_id,
                "claim_id": claim_id,
                "lean_decl": lean_decl,
                "file_path": file_path,
                "proof_status": proof_status,
                "verification_boundary": verification_boundary,
                "reviewer_status": reviewer_status,
                "dependency_ids": [],
                "executable_links": [],
            }
        )
    return cards


def _status_to_boundary(status: str) -> str:
    """Map claim status to verification boundary."""
    if status == "machine_checked":
        return "fully_machine_checked"
    if status == "linked_to_kernel":
        return "numerically_witnessed"
    return "human_review_only"


def write_theorem_cards(paper_dir: Path, paper_id: str) -> list[dict]:
    """Derive theorem cards and write theorem_cards.json. Returns the list of cards."""
    cards = derive_theorem_cards(paper_dir, paper_id)
    if cards:
        paper_dir.joinpath("theorem_cards.json").write_text(
            json.dumps(cards, indent=2), encoding="utf-8"
        )
    return cards
