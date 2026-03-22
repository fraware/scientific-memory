# LLM evaluation fixtures (non-canonical)

This directory holds **reference proposal bundles** used by the `llm_eval` benchmark task ([`benchmarks/tasks/llm_eval/scorer.py`](../tasks/llm_eval/scorer.py)) and by [`pipeline/tests/test_llm_eval_harness.py`](../../pipeline/tests/test_llm_eval_harness.py). These files are **not** part of the corpus and are **not** ingested by the portal.

## Layout

- One subdirectory per paper id (must match `corpus/papers/<id>/`).
- Optional files (any subset):
  - `reference_llm_claim_proposals.json` — reviewed bundle; gold-id recall is computed vs `benchmarks/gold/<id>/claims.json`.
  - `reference_llm_mapping_proposals.json` — reviewed bundle; precision/recall vs `corpus/papers/<id>/mapping.json` `claim_to_decl`.
  - `reference_llm_lean_proposals.json` — reviewed bundle; static conversion-ready checks against the real Lean file on disk.

## Scored metrics

The `llm_eval` scorer computes deterministic static metrics from the reference bundles, including:
- Claim ID recall/precision/F1 against `benchmarks/gold/<paper_id>/claims.json` (`gold_claim_id_*`).
- Mapping key recall/precision/F1 against `corpus/papers/<paper_id>/mapping.json` (`mapping_keys_*`).
- Lean edit conversion readiness (`lean_reference_conversion_ready`).
- Disagreement rates for claims and mapping (`*_disagreement_rate_micro`).
- Promotion outcome counters and acceptance rate when `metadata.reviewer_decision` is present.
- Reviewer time aggregation when `metadata.reviewer_time_seconds` is present
  (`reviewer_time_seconds_total`, `reviewer_time_observations`).

## When prompts change

1. Re-run generation (fake or live) if you intentionally change model behavior expectations.
2. Update reference JSON only after human review.
3. Update [`docs/testing/llm-lean-live-test-matrix.md`](../../docs/testing/llm-lean-live-test-matrix.md) evidence log if you run live checks.

## Regression expectations

Gate 6 thresholds for this task live in `benchmarks/baseline_thresholds.json`
under `tasks.llm_eval`. If you intentionally change fixture coverage or scoring
semantics, update both the reference bundles and those thresholds in the same PR.

## Live evaluation reports

Operator runs ([`scripts/llm_live_eval.py`](../../scripts/llm_live_eval.py)) write `benchmarks/reports/llm_live_*.json`; those paths are gitignored by default.
