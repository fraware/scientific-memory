"""Benchmark slice: reference LLM proposal bundles under
`benchmarks/llm_eval/` (regression anchors).

Each subdirectory named like a paper_id may contain optional:
- reference_llm_claim_proposals.json
- reference_llm_mapping_proposals.json
- reference_llm_lean_proposals.json

Metrics (deterministic, no live API):
- **gold_claim_id_recall_micro**: Among papers with gold claims + reference claim bundle, fraction of
  gold claim ids that appear as proposal.claim.id in the reference bundle (micro-averaged).
- **mapping_keys_recall_micro** / **mapping_keys_precision_micro**: Compare reference mapping proposals
  to corpus ``corpus/papers/<id>/mapping.json`` ``claim_to_decl`` (exact short_name match).
- **lean_reference_conversion_ready**: Proposals in reference lean bundles with non-empty replacements,
  target_file under formal/, no ``..``, and each ``find`` occurring exactly once in the target file.

These files are not canonical corpus data; they are reviewed regression
fixtures (see `benchmarks/llm_eval/README.md`).
"""

from __future__ import annotations

import json
from pathlib import Path

from sm_pipeline.models.llm_proposals import (
    LlmClaimProposalsBundle,
    LlmLeanProposalsBundle,
    LlmMappingProposalsBundle,
)


def _gold_claim_ids(repo_root: Path, paper_id: str) -> set[str]:
    path = repo_root / "benchmarks" / "gold" / paper_id / "claims.json"
    if not path.is_file():
        return set()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return set()
    if not isinstance(data, list):
        return set()
    return {str(c.get("id")) for c in data if isinstance(c, dict) and c.get("id")}


def _corpus_mapping_claim_to_decl(repo_root: Path, paper_id: str) -> dict[str, str]:
    path = repo_root / "corpus" / "papers" / paper_id / "mapping.json"
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}
    if not isinstance(data, dict):
        return {}
    raw = data.get("claim_to_decl")
    if not isinstance(raw, dict):
        return {}
    return {str(k): str(v) for k, v in raw.items() if k is not None}


def _lean_find_unique_count(repo_root: Path, target_file: str, find: str) -> int:
    clean_target = target_file.replace("\\", "/")
    path = repo_root / clean_target
    if not path.is_file():
        return 0
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return 0
    if not find:
        return 0
    return text.count(find)


def run(repo_root: Path) -> dict:
    repo_root = repo_root.resolve()
    base = repo_root / "benchmarks" / "llm_eval"
    out: dict = {
        "cases_scanned": 0,
        "reference_claim_bundles": 0,
        "reference_mapping_bundles": 0,
        "reference_lean_bundles": 0,
        "gold_claim_id_hits": 0,
        "gold_claim_id_total": 0,
        "gold_claim_id_recall_micro": 1.0,
        "gold_claim_id_precision_micro": 1.0,
        "gold_claim_id_f1_micro": 1.0,
        "claim_disagreement_rate_micro": 0.0,
        "mapping_tp": 0,
        "mapping_proposal_count": 0,
        "mapping_gold_key_count": 0,
        "mapping_keys_precision_micro": 1.0,
        "mapping_keys_recall_micro": 1.0,
        "mapping_keys_f1_micro": 1.0,
        "mapping_disagreement_rate_micro": 0.0,
        "lean_reference_proposals_total": 0,
        "lean_reference_conversion_ready": 0,
        "promotion_decisions_total": 0,
        "promotion_accepted_total": 0,
        "promotion_rejected_total": 0,
        "promotion_edited_total": 0,
        "promotion_pending_total": 0,
        "promotion_acceptance_rate": 0.0,
        "reviewer_time_seconds_total": 0.0,
        "reviewer_time_observations": 0,
    }
    if not base.is_dir():
        return out

    claim_hits = 0
    claim_gold_total = 0
    claim_proposed_total = 0
    map_tp = 0
    map_prop_n = 0
    map_gold_n = 0
    lean_total = 0
    lean_ready = 0
    promo_total = 0
    promo_accepted = 0
    promo_rejected = 0
    promo_edited = 0
    promo_pending = 0
    reviewer_time_total = 0.0
    reviewer_time_n = 0

    for case_dir in sorted(p for p in base.iterdir() if p.is_dir()):
        paper_id = case_dir.name
        has_ref = any(
            (case_dir / n).is_file()
            for n in (
                "reference_llm_claim_proposals.json",
                "reference_llm_mapping_proposals.json",
                "reference_llm_lean_proposals.json",
            )
        )
        if has_ref:
            out["cases_scanned"] += 1

        ref_claim = case_dir / "reference_llm_claim_proposals.json"
        if ref_claim.is_file():
            out["reference_claim_bundles"] += 1
            try:
                raw = json.loads(ref_claim.read_text(encoding="utf-8"))
                bundle = LlmClaimProposalsBundle.model_validate(raw)
            except (json.JSONDecodeError, OSError, ValueError):
                bundle = None
            gold_ids = _gold_claim_ids(repo_root, paper_id)
            if gold_ids and bundle is not None:
                proposed_ids = {p.claim.id for p in bundle.proposals}
                claim_gold_total += len(gold_ids)
                claim_hits += len(gold_ids & proposed_ids)
                claim_proposed_total += len(proposed_ids)
            # Promotion metrics: only counted when a decision is present.
            if bundle is not None and bundle.metadata is not None:
                decision = bundle.metadata.reviewer_decision
                if decision:
                    promo_total += 1
                    if decision == "accepted":
                        promo_accepted += 1
                    elif decision == "rejected":
                        promo_rejected += 1
                    elif decision == "edited":
                        promo_edited += 1
                    elif decision == "pending":
                        promo_pending += 1
                rt = bundle.metadata.reviewer_time_seconds
                if rt is not None:
                    reviewer_time_total += float(rt)
                    reviewer_time_n += 1

        ref_map = case_dir / "reference_llm_mapping_proposals.json"
        if ref_map.is_file():
            out["reference_mapping_bundles"] += 1
            try:
                raw = json.loads(ref_map.read_text(encoding="utf-8"))
                mbundle = LlmMappingProposalsBundle.model_validate(raw)
            except (json.JSONDecodeError, OSError, ValueError):
                mbundle = None
            c2d = _corpus_mapping_claim_to_decl(repo_root, paper_id)
            if c2d and mbundle is not None:
                map_gold_n += len(c2d)
                for p in mbundle.proposals:
                    map_prop_n += 1
                    exp = c2d.get(p.claim_id)
                    if exp is not None and p.lean_declaration_short_name == exp:
                        map_tp += 1
            if mbundle is not None and mbundle.metadata is not None:
                decision = mbundle.metadata.reviewer_decision
                if decision:
                    promo_total += 1
                    if decision == "accepted":
                        promo_accepted += 1
                    elif decision == "rejected":
                        promo_rejected += 1
                    elif decision == "edited":
                        promo_edited += 1
                    elif decision == "pending":
                        promo_pending += 1

        ref_lean = case_dir / "reference_llm_lean_proposals.json"
        if ref_lean.is_file():
            out["reference_lean_bundles"] += 1
            try:
                raw = json.loads(ref_lean.read_text(encoding="utf-8"))
                lbundle = LlmLeanProposalsBundle.model_validate(raw)
            except (json.JSONDecodeError, OSError, ValueError):
                lbundle = None
            if lbundle is not None:
                if lbundle.metadata is not None:
                    decision = lbundle.metadata.reviewer_decision
                    if decision:
                        promo_total += 1
                        if decision == "accepted":
                            promo_accepted += 1
                        elif decision == "rejected":
                            promo_rejected += 1
                        elif decision == "edited":
                            promo_edited += 1
                        elif decision == "pending":
                            promo_pending += 1
                for p in lbundle.proposals:
                    lean_total += 1
                    tf = (p.target_file or "").strip().replace("\\", "/")
                    if not tf.startswith("formal/") or ".." in tf:
                        continue
                    reps = p.replacements
                    if not reps:
                        continue
                    ok = True
                    for r in reps:
                        if _lean_find_unique_count(repo_root, tf, r.find) != 1:
                            ok = False
                            break
                    if ok:
                        lean_ready += 1

    out["gold_claim_id_hits"] = claim_hits
    out["gold_claim_id_total"] = claim_gold_total
    if claim_gold_total > 0:
        out["gold_claim_id_recall_micro"] = round(claim_hits / claim_gold_total, 6)
    if claim_proposed_total > 0:
        precision = claim_hits / claim_proposed_total
        out["gold_claim_id_precision_micro"] = round(precision, 6)
        out["claim_disagreement_rate_micro"] = round(1.0 - precision, 6)
        recall = out.get("gold_claim_id_recall_micro", 0.0) or 0.0
        if precision + recall > 0:
            out["gold_claim_id_f1_micro"] = round(
                2.0 * precision * recall / (precision + recall), 6
            )

    out["mapping_tp"] = map_tp
    out["mapping_proposal_count"] = map_prop_n
    out["mapping_gold_key_count"] = map_gold_n
    if map_prop_n > 0:
        out["mapping_keys_precision_micro"] = round(map_tp / map_prop_n, 6)
    if map_gold_n > 0:
        out["mapping_keys_recall_micro"] = round(map_tp / map_gold_n, 6)
    prec = out.get("mapping_keys_precision_micro") or 0.0
    rec = out.get("mapping_keys_recall_micro") or 0.0
    if prec + rec > 0:
        out["mapping_keys_f1_micro"] = round(2.0 * prec * rec / (prec + rec), 6)
        out["mapping_disagreement_rate_micro"] = round(1.0 - prec, 6)

    out["lean_reference_proposals_total"] = lean_total
    out["lean_reference_conversion_ready"] = lean_ready
    out["promotion_decisions_total"] = promo_total
    out["promotion_accepted_total"] = promo_accepted
    out["promotion_rejected_total"] = promo_rejected
    out["promotion_edited_total"] = promo_edited
    out["promotion_pending_total"] = promo_pending
    if promo_total > 0:
        out["promotion_acceptance_rate"] = round(promo_accepted / promo_total, 6)
    out["reviewer_time_seconds_total"] = round(reviewer_time_total, 6)
    out["reviewer_time_observations"] = reviewer_time_n
    return out
