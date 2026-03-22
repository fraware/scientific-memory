# Gold benchmark fixtures

Gold fixtures are human-reviewed references used by the `gold` benchmark task.

Layout per paper:

- `benchmarks/gold/<paper_id>/claims.json` (required for claim metrics)
- `benchmarks/gold/<paper_id>/assumptions.json` (optional)
- `benchmarks/gold/<paper_id>/source_spans.json` (optional alignment checks)

Matching is deterministic by `id` against corpus data for the same paper.

## Workflow

1. Scaffold from canonical corpus:
   - `just scaffold-gold <paper_id>`
2. Curate fixtures by hand.
3. Run `just benchmark`.
4. If expected outputs changed, update `benchmarks/baseline_thresholds.json`.

Use this for non-scaffold papers admitted to `corpus/index.json`; keep intake
scaffolds out of gold until they have real extracted/formalized artifacts.
