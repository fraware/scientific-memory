# Assurance benchmarks (Gate 6)

Offline Gate 6 task `assurance` scores `corpus/assurance/` via `benchmarks/tasks/assurance/scorer.py`.

## Floors

- `expected_floors.json` — human-readable floor notes for pilot ingest
- `benchmarks/baseline_thresholds.json` → `tasks.assurance` — enforced by `just benchmark` / `sm-pipeline benchmark`

## Reproducible metrics gold

Pinned snapshot: `expected_metrics.json` (mirrors `examples/assurance-pilot/metrics.json`).

Regenerate after intentional pilot changes:

```bash
uv run --project pipeline sm metrics autonomous-science --out examples/assurance-pilot/metrics.json
cp examples/assurance-pilot/metrics.json benchmarks/assurance/expected_metrics.json
```

Denominator rule: for every metric slice, `len(included_ids) + len(exclusions) == len(population_action_ids)`.

## Non-claims

These floors measure reconstruction and evidence-node presence for synthetic pilots. They are not live authorization success rates and do not rewrite claim status.

See [docs/assurance/](../../docs/assurance/README.md).
