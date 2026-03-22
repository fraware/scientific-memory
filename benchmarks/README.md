# Benchmarks

Benchmark regression is Gate 6. Run from repo root:

```bash
just benchmark
```

The run writes `benchmarks/reports/latest.json` and compares results against
`benchmarks/baseline_thresholds.json` (`tasks` minima and optional
`tasks_ceiling` maxima). CI enforces this in the benchmark workflows.

## Folder guide

- [`tasks/`](tasks/README.md): deterministic benchmark scorers
- [`gold/`](gold/README.md): human-reviewed gold labels per paper
- [`llm_eval/`](llm_eval/README.md): reviewed LLM reference bundles used as
  regression anchors
- `reports/`: generated outputs (`latest.json`, trend history, summaries)
- `baseline_thresholds.json`: Gate 6 regression floors/ceilings

## What is enforced today

- `tasks.extraction` / `tasks.mapping`: corpus extraction and mapping floors
  across the admitted index.
- `tasks.theorem_cards`: declaration and machine-checked floors for formalized
  papers.
- `tasks.gold`: precision/recall floors plus
  `tasks_ceiling.gold.source_span_alignment_error_rate`.
- `tasks.llm_suggestions` / `tasks.llm_lean_suggestions`: observability counters
  for optional non-canonical sidecars (`llm_*_proposals.json`,
  `suggested_*.json`).
- `tasks.llm_eval`: regression over reviewed reference bundles in
  `benchmarks/llm_eval/`, including disagreement fields, promotion counters, and
  reviewer-time aggregation.

## Current corpus and gold policy

The corpus index currently contains eight papers. Six formalized core papers
have gold fixtures, while two hard-dimension stress scaffolds are intake-only.
`baseline_thresholds.json` reflects this by keeping `tasks.gold.papers_with_gold`
at `6`.

For each new non-scaffold paper admitted to `corpus/index.json`, add
`benchmarks/gold/<paper_id>/` in the same PR (use `just scaffold-gold <paper_id>`
as a starting point), then adjust benchmark thresholds as needed.

## Related docs

- [Metrics](../docs/metrics.md)
- [Generated artifacts](../docs/generated-artifacts.md)
- [ADR 0013 LLM evaluation policy](../docs/adr/0013-llm-evaluation-policy.md)
