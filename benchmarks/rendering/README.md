# PCS rendering benchmarks

Scientific Memory evidence-layer benchmarks for PCS release import, portal read-model
rendering, query correctness, release comparison, and failed-release interpretability.

## Layout

Each case directory contains:

- `case.json` — case metadata and fixture pointer
- `release_manifest.v0.json` — manifest alias (artifacts resolve via `fixture_dir`)
- `expected_sections.json` — required interpretability sections
- `expected_queries.json` — CLI query expectations
- `expected_lineage.json` — lineage fields after import
- `expected_staleness.json` — staleness expectations
- `expected_compare.json` — release comparison expectations (when applicable)
- `expected_failure.json` — failure-evidence checks (failed cases only)

### Success-path cases

- `labtrust_qc_release/`
- `tool_use_safety/`
- `computation_reproducibility/`

### Failed-release cases

Under `failed/`:

- `rejected_certificate/` — computation witness rejected
- `stale_release/` — stale lineage after bundle drift
- `failed_lean_check/` — formal kernel failed obligation (read-model evidence)
- `failed_pf_verification/` — PF explain on failed formal check
- `missing_registry_metadata/` — deferred registry checks in read model

## Run

```bash
just pcs-benchmark-rendering CASES=benchmarks/rendering/labtrust_qc_release OUT=benchmark_runs/labtrust_rendering

just pcs-benchmark-rendering-all OUT=benchmark_runs/pcs_rendering

python -m sm_pipeline.benchmark.rendering --cases benchmarks/rendering --out benchmark_runs/pcs_rendering
```

Reports are written to:

- `rendering_benchmark_report.json` — full case results (`PcsRenderingBenchmarkReport.v0`)
- `pcs_bench_payload.json` — flattened metrics for **pcs-bench**
- `rendering_benchmark_summary.md` — human-readable summary

Regression floors: `baseline_thresholds.json` (enforced by default via `--check-regression`).

## Regenerate expectations

After fixture or import changes:

```bash
python scripts/bootstrap_pcs_rendering_benchmarks.py
```
