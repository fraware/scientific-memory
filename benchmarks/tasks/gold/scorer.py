"""Gold benchmark: papers with gold labels and extraction quality (precision/recall/F1).

Matching contract (deterministic):
- Claims: corpus and gold claim lists are matched by `id`. A claim is a true positive
  if the same id exists in both corpus and gold for that paper.
- Assumptions: same by `id` when both corpus and gold have assumptions for the paper.
- Precision = TP / |corpus|, Recall = TP / |gold|, F1 = 2*P*R/(P+R) (0 when denominators 0).
- Aggregates are micro-averaged over all papers with gold (sum(TP)/sum(corpus), etc.).
"""

import json
from pathlib import Path

from sm_pipeline.metrics.source_span_alignment import compute_source_span_alignment


def _attach_source_span_alignment(repo_root: Path, out: dict) -> None:
    """Merge source-span alignment vs gold reference into benchmark gold task output."""
    align = compute_source_span_alignment(repo_root)
    out["source_span_total_compared"] = int(align.get("total_compared") or 0)
    out["source_span_alignment_error_count"] = int(align.get("alignment_error_count") or 0)
    rate = align.get("alignment_error_rate")
    if rate is not None:
        out["source_span_alignment_error_rate"] = float(rate)


def run(repo_root: Path) -> dict:
    """
    Compute gold metrics: papers_with_gold, counts, and when corpus exists for same papers,
    gold_claim_precision, gold_claim_recall, gold_claim_f1; same for assumptions when present.
    """
    repo_root = Path(repo_root).resolve()
    gold_root = repo_root / "benchmarks" / "gold"
    papers_dir = repo_root / "corpus" / "papers"
    if not gold_root.is_dir():
        out = _empty()
        _attach_source_span_alignment(repo_root, out)
        return out

    papers_with_gold = 0
    gold_claim_count = 0
    # For precision/recall: aggregate TP and total corpus/gold counts across papers
    claim_tp = 0
    claim_corpus_total = 0
    claim_gold_total = 0
    assumption_tp = 0
    assumption_corpus_total = 0
    assumption_gold_total = 0

    for path in sorted(gold_root.iterdir()):
        if not path.is_dir():
            continue
        paper_id = path.name
        gold_claims_path = path / "claims.json"
        if not gold_claims_path.exists():
            continue
        try:
            gold_claims = json.loads(gold_claims_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        if not isinstance(gold_claims, list) or len(gold_claims) == 0:
            continue

        papers_with_gold += 1
        gold_ids = {str(c.get("id")) for c in gold_claims if isinstance(c, dict) and c.get("id")}
        gold_claim_count += len(gold_ids)

        corpus_claims_path = papers_dir / paper_id / "claims.json"
        if corpus_claims_path.exists():
            try:
                corpus_claims = json.loads(corpus_claims_path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                corpus_claims = []
        else:
            corpus_claims = []
        if not isinstance(corpus_claims, list):
            corpus_claims = []
        corpus_ids = {str(c.get("id")) for c in corpus_claims if isinstance(c, dict) and c.get("id")}
        tp = len(corpus_ids & gold_ids)
        claim_tp += tp
        claim_corpus_total += len(corpus_ids)
        claim_gold_total += len(gold_ids)

        gold_assum_path = path / "assumptions.json"
        corpus_assum_path = papers_dir / paper_id / "assumptions.json"
        if gold_assum_path.exists() and corpus_assum_path.exists():
            try:
                gold_assum = json.loads(gold_assum_path.read_text(encoding="utf-8"))
                corpus_assum = json.loads(corpus_assum_path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                gold_assum = []
                corpus_assum = []
            if not isinstance(gold_assum, list):
                gold_assum = []
            if not isinstance(corpus_assum, list):
                corpus_assum = []
            gold_a_ids = {str(a.get("id")) for a in gold_assum if isinstance(a, dict) and a.get("id")}
            corpus_a_ids = {str(a.get("id")) for a in corpus_assum if isinstance(a, dict) and a.get("id")}
            assumption_tp += len(corpus_a_ids & gold_a_ids)
            assumption_corpus_total += len(corpus_a_ids)
            assumption_gold_total += len(gold_a_ids)

    out = {
        "papers_with_gold": papers_with_gold,
        "gold_claim_count": gold_claim_count,
    }

    if claim_gold_total > 0 or claim_corpus_total > 0:
        prec = (claim_tp / claim_corpus_total) if claim_corpus_total else 0.0
        rec = (claim_tp / claim_gold_total) if claim_gold_total else 0.0
        f1 = (2 * prec * rec / (prec + rec)) if (prec + rec) else 0.0
        out["gold_claim_precision"] = round(prec, 4)
        out["gold_claim_recall"] = round(rec, 4)
        out["gold_claim_f1"] = round(f1, 4)

    if assumption_gold_total > 0 or assumption_corpus_total > 0:
        prec_a = (assumption_tp / assumption_corpus_total) if assumption_corpus_total else 0.0
        rec_a = (assumption_tp / assumption_gold_total) if assumption_gold_total else 0.0
        f1_a = (2 * prec_a * rec_a / (prec_a + rec_a)) if (prec_a + rec_a) else 0.0
        out["gold_assumption_precision"] = round(prec_a, 4)
        out["gold_assumption_recall"] = round(rec_a, 4)
        out["gold_assumption_f1"] = round(f1_a, 4)

    _attach_source_span_alignment(repo_root, out)
    return out


def _empty() -> dict:
    return {
        "papers_with_gold": 0,
        "gold_claim_count": 0,
    }
