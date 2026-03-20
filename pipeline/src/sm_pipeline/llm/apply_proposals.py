"""Human-gated apply: merge reviewed LLM proposals into canonical corpus JSON."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from sm_pipeline.models.claim import Claim
from sm_pipeline.models.llm_proposals import LlmClaimProposalsBundle, LlmMappingProposalsBundle


def load_claim_bundle(path: Path) -> LlmClaimProposalsBundle:
    data = json.loads(path.read_text(encoding="utf-8"))
    return LlmClaimProposalsBundle.model_validate(data)


def load_mapping_bundle(path: Path) -> LlmMappingProposalsBundle:
    data = json.loads(path.read_text(encoding="utf-8"))
    return LlmMappingProposalsBundle.model_validate(data)


def preview_apply_claim_proposals(
    repo_root: Path, bundle_path: Path
) -> tuple[list[dict], list[dict]]:
    """Return (before_claims, after_claims) as JSON-serializable lists."""
    repo_root = repo_root.resolve()
    bundle = load_claim_bundle(bundle_path)
    paper_dir = repo_root / "corpus" / "papers" / bundle.paper_id
    claims_path = paper_dir / "claims.json"
    before = json.loads(claims_path.read_text(encoding="utf-8"))
    if not isinstance(before, list):
        raise TypeError("claims.json must be a list")
    after = _merge_claims(before, bundle)
    return before, after


def apply_claim_proposals(repo_root: Path, bundle_path: Path) -> Path:
    """Write claims.json after merging proposal claims (upsert by id)."""
    repo_root = repo_root.resolve()
    bundle = load_claim_bundle(bundle_path)
    paper_dir = repo_root / "corpus" / "papers" / bundle.paper_id
    claims_path = paper_dir / "claims.json"
    before = json.loads(claims_path.read_text(encoding="utf-8"))
    if not isinstance(before, list):
        raise TypeError("claims.json must be a list")
    after = _merge_claims(before, bundle)
    claims_path.write_text(json.dumps(after, indent=2), encoding="utf-8")
    return claims_path


def _merge_claims(existing: list[Any], bundle: LlmClaimProposalsBundle) -> list[dict]:
    by_id: dict[str, dict] = {}
    order: list[str] = []
    for row in existing:
        if isinstance(row, dict) and row.get("id"):
            cid = str(row["id"])
            if cid not in by_id:
                order.append(cid)
            by_id[cid] = dict(row)
    for entry in bundle.proposals:
        c = Claim.model_validate(entry.claim.model_dump())
        if c.paper_id != bundle.paper_id:
            raise ValueError(
                f"Proposal claim id={c.id} has paper_id={c.paper_id!r}, expected {bundle.paper_id!r}"
            )
        if c.id not in by_id:
            order.append(c.id)
        by_id[c.id] = c.model_dump(mode="json")
    return [by_id[k] for k in order]


def preview_apply_mapping_proposals(repo_root: Path, bundle_path: Path) -> tuple[dict, dict]:
    repo_root = repo_root.resolve()
    bundle = load_mapping_bundle(bundle_path)
    paper_dir = repo_root / "corpus" / "papers" / bundle.paper_id
    mapping_path = paper_dir / "mapping.json"
    before = json.loads(mapping_path.read_text(encoding="utf-8"))
    if not isinstance(before, dict):
        raise TypeError("mapping.json must be an object")
    after = _merge_mapping(before, bundle)
    return before, after


def apply_mapping_proposals(repo_root: Path, bundle_path: Path) -> Path:
    repo_root = repo_root.resolve()
    bundle = load_mapping_bundle(bundle_path)
    paper_dir = repo_root / "corpus" / "papers" / bundle.paper_id
    mapping_path = paper_dir / "mapping.json"
    before = json.loads(mapping_path.read_text(encoding="utf-8"))
    if not isinstance(before, dict):
        raise TypeError("mapping.json must be an object")
    after = _merge_mapping(before, bundle)
    mapping_path.write_text(json.dumps(after, indent=2), encoding="utf-8")
    return mapping_path


def _merge_mapping(existing: dict[str, Any], bundle: LlmMappingProposalsBundle) -> dict[str, Any]:
    out = dict(existing)
    if out.get("paper_id") != bundle.paper_id:
        raise ValueError(
            f"mapping paper_id {out.get('paper_id')!r} does not match bundle {bundle.paper_id!r}"
        )
    c2d = dict(out.get("claim_to_decl") or {})
    for p in bundle.proposals:
        c2d[p.claim_id] = p.lean_declaration_short_name
    out["claim_to_decl"] = dict(sorted(c2d.items()))
    return out
