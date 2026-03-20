# Benchmarks

Extraction, mapping, and theorem-card benchmark tasks. Each task lives under `tasks/<name>/` with a `scorer.py` that emits JSON. Run from repo root: `just benchmark`. Reports are written to `reports/` (e.g. `latest.json`). CI runs the benchmark with regression check (Gate 6) against `baseline_thresholds.json`; see [docs/generated-artifacts.md](../docs/generated-artifacts.md).

## Gold task

The gold task runs when `benchmarks/tasks/gold/scorer.py` exists. When `benchmarks/gold/<paper_id>/claims.json` (or `assumptions.json`) exists, the benchmark computes precision/recall/F1. Source-span alignment metrics are merged into `tasks.gold` whenever gold `source_spans.json` files exist. In this repository, `baseline_thresholds.json` enforces `papers_with_gold` for every paper in `corpus/index.json` and a ceiling on `source_span_alignment_error_rate`; new forks may relax those thresholds.

**Gold-creation workflow:** The admitted corpus has six papers; each has gold under `benchmarks/gold/<paper_id>/` (baseline enforces `papers_with_gold`). For every **new** paper added to `corpus/index.json`, create `benchmarks/gold/<paper_id>/` as part of intake or first-artifact. Run `just scaffold-gold <paper_id>` to scaffold from the corpus (claims, source_spans from claim source_span, assumptions); then curate as needed. Or add `claims.json` and/or `assumptions.json` (same schema as corpus) and optionally `source_spans.json` (list of `{ "claim_id", "source_span" }`) by hand. Matching is by `id`. Gate 6 regression includes `tasks_ceiling.gold.source_span_alignment_error_rate` in `baseline_thresholds.json`. See [docs/metrics.md](../docs/metrics.md)#gold-labels-extraction-precisionrecall.
