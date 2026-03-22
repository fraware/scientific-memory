# Benchmark tasks

Each benchmark task lives in `tasks/<task_name>/scorer.py` and exports a
deterministic `run(repo_root: Path) -> dict` result.

Current tasks:

- `extraction`: claim/source-span/assumption inventory across the corpus
- `mapping`: `claim_to_decl` coverage and completeness
- `theorem_cards`: declaration and machine-checked counts, plus per-paper slices
- `gold`: precision/recall/F1 and source-span alignment against
  `benchmarks/gold/`
- `llm_suggestions`: optional sidecar footprint (`llm_*`, `suggested_*`)
- `llm_lean_suggestions`: Lean sidecar footprint and conversion-ready checks
- `llm_eval`: reviewed reference-bundle regression under `benchmarks/llm_eval/`

## Add or modify a task

1. Update the task scorer under `tasks/<name>/scorer.py`.
2. Ensure the task is wired by the benchmark runner in the pipeline.
3. Run `just benchmark` and inspect `benchmarks/reports/latest.json`.
4. Update `benchmarks/baseline_thresholds.json` when intended outputs change.
5. Update `docs/metrics.md` when metric semantics change.
