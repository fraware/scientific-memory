# Benchmarks

Extraction, mapping, theorem-card, and LLM evaluation benchmark tasks. Each task lives under `tasks/<name>/` with a `scorer.py` that emits JSON. Run from repo root: `just benchmark`. Reports are written to `reports/` (e.g. `latest.json`). CI runs the benchmark with regression check (Gate 6) against `baseline_thresholds.json`; see [docs/generated-artifacts.md](../docs/generated-artifacts.md).

## Gold task

The gold task runs when `benchmarks/tasks/gold/scorer.py` exists. When `benchmarks/gold/<paper_id>/claims.json` (or `assumptions.json`) exists, the benchmark computes precision/recall/F1. Source-span alignment metrics are merged into `tasks.gold` whenever gold `source_spans.json` files exist. In this repository, `baseline_thresholds.json` enforces `papers_with_gold` for every paper in `corpus/index.json` and a ceiling on `source_span_alignment_error_rate`; new forks may relax those thresholds.

## LLM evaluation tasks

**LLM suggestions observability:** Tasks `llm_suggestions` and `llm_lean_suggestions` track optional sidecar files (`llm_claim_proposals.json`, `llm_mapping_proposals.json`, `llm_lean_proposals.json`) under paper directories. These are non-canonical, human-review-only artifacts; thresholds default to zero until you raise floors.

**LLM eval regression:** Task `llm_eval` scores reviewed reference bundles under [`benchmarks/llm_eval/<paper_id>/`](llm_eval/README.md) (`reference_llm_*_proposals.json`) against gold claim IDs, corpus `mapping.json`, and static Lean conversion-ready checks. Declared prompt template digests appear at top level of the benchmark report as `llm_prompt_templates` (id → SHA-256). See [docs/adr/0013-llm-evaluation-policy.md](../docs/adr/0013-llm-evaluation-policy.md) and [docs/testing/llm-human-eval-rubric.md](../docs/testing/llm-human-eval-rubric.md).

**Gold-creation workflow:** The admitted corpus has six papers; each has gold under `benchmarks/gold/<paper_id>/` (baseline enforces `papers_with_gold`). For every **new** paper added to `corpus/index.json`, create `benchmarks/gold/<paper_id>/` as part of intake or first-artifact. Run `just scaffold-gold <paper_id>` to scaffold from the corpus (claims, source_spans from claim source_span, assumptions); then curate as needed. Or add `claims.json` and/or `assumptions.json` (same schema as corpus) and optionally `source_spans.json` (list of `{ "claim_id", "source_span" }`) by hand. Matching is by `id`. Gate 6 regression includes `tasks_ceiling.gold.source_span_alignment_error_rate` in `baseline_thresholds.json`. See [docs/metrics.md](../docs/metrics.md)#gold-labels-extraction-precisionrecall.
