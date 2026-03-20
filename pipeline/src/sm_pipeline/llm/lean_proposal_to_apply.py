"""Convert a reviewed llm_lean_proposals entry into a proof_repair_apply_bundle."""

from __future__ import annotations

import json
from pathlib import Path

from sm_pipeline.models.llm_proposals import LlmLeanProposalsBundle


def lean_proposal_to_apply_bundle_dict(
    bundle: dict, *, proposal_id: str, review_record_path: str | None = None
) -> dict:
    """
    Build a dict conforming to proof_repair_apply_bundle.schema.json from one Lean proposal.

    Raises ValueError if the proposal is missing, has no replacements, or paths are unsafe.
    """
    model = LlmLeanProposalsBundle.model_validate(bundle)
    entry = next((p for p in model.proposals if p.proposal_id == proposal_id), None)
    if entry is None:
        raise ValueError(f"No proposal with proposal_id={proposal_id!r}")
    if not entry.replacements:
        raise ValueError(
            "Proposal has empty replacements; add find/replace pairs before converting, "
            "or draft manually for proof-repair-apply"
        )
    rel = entry.target_file.strip().replace("\\", "/")
    if not rel.startswith("formal/") or ".." in rel:
        raise ValueError(f"Unsafe or invalid target_file: {rel!r}")
    out: dict = {
        "verification_boundary": "human_review_only",
        "patches": [
            {
                "relative_path": rel,
                "replacements": [
                    {"find": r.find, "replace": r.replace} for r in entry.replacements
                ],
            }
        ],
    }
    if review_record_path:
        out["review_record_path"] = review_record_path
    return out


def write_apply_bundle_from_lean_proposals_file(
    lean_bundle_path: Path,
    proposal_id: str,
    output_path: Path,
    *,
    review_record_path: str | None = None,
) -> Path:
    data = json.loads(Path(lean_bundle_path).read_text(encoding="utf-8"))
    apply_bundle = lean_proposal_to_apply_bundle_dict(
        data, proposal_id=proposal_id, review_record_path=review_record_path
    )
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(apply_bundle, indent=2), encoding="utf-8")
    return output_path
