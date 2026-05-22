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
- `formal_trust_kernel/` — LabTrust release with formal trust kernel emphasis

### Failed-release cases

Under `failed/`:

- `rejected_certificate/` — computation witness rejected
- `stale_release/` — stale lineage after bundle drift
- `failed_lean_check/` — formal kernel failed obligation (read-model evidence)
- `failed_pf_verification/` — PF explain on failed formal check
- `missing_registry_metadata/` — deferred registry checks in read model
- `result_hash_mismatch/` — computation witness result hash mismatch

## Run

```bash
just pcs-benchmark-rendering CASES=benchmarks/rendering/labtrust_qc_release OUT=benchmark_runs/labtrust_rendering

just pcs-benchmark-rendering-all OUT=benchmark_runs/pcs_rendering

python -m sm_pipeline.benchmark.pcs_rendering --cases benchmarks/rendering --out benchmark_runs/pcs_rendering
```

Reports are written to (validated against `schemas/pcs/benchmark/*.schema.json`):

- `benchmark_run.v0.json` — aggregate run summary for **pcs-bench**
- `rendering_coverage_report.v0.json` — section coverage per success case
- `query_coverage_report.v0.json` — query and compare coverage
- `failed_release_rendering_report.v0.json` — failure-evidence rendering for failed cases
- `pcs_bench_ingest.v0.json` — **canonical pcs-bench ingest** (embedded `BenchmarkRun.v0`, `CoverageReport.v0`, `FailureLocalizationResult.v0`, `ExplainQualityReport.v0`, plus `artifact_refs`)
- `explain_quality_reports/` — per-case `ExplainQualityReport.v0` sidecars referenced from ingest
- `coverage_reports/` — per-metric `CoverageReport.v0` sidecars referenced from ingest
- `benchmark_runs/` — per-case `BenchmarkRun.v0` sidecars (multi-case suites)
- `failure_localization_reports/` — `FailureLocalizationResult.v0` sidecars for failure-mode cases
- `pcs_bench_payload.json` — legacy flattened alias

### External reviewer minimal packet

`external_reviewer_minimal/` — five cases for external review and pcs-bench smoke ingest (see `external_reviewer_minimal/README.md`).

### Release-grade producer

```bash
make pcs-bench-producer
just pcs-bench-producer-gate
just pcs-bench-producer-gate-external
```
- `rendering_benchmark_summary.md` — human-readable summary

Validate a completed run (auto-detects adjacent `pcs-core` for schema + semantic checks when present):

```bash
just validate-pcs-benchmark-output-pcs-core benchmark_runs/pcs_rendering ../pcs-core

python scripts/validate_pcs_benchmark_output.py benchmark_runs/pcs_rendering
python scripts/package_pcs_bench_bundle.py benchmark_runs/pcs_rendering --validate-pcs-core-output ../pcs-core
```

pcs-bench contract: [docs/pcs-bench-ingest.md](../../docs/pcs-bench-ingest.md). Suite registry: [benchmarks/pcs_bench/suite_registry.v0.json](../pcs_bench/suite_registry.v0.json).

Regression floors: `baseline_thresholds.json` (enforced by default via `--check-regression`).

## Regenerate expectations

After fixture or import changes:

```bash
python scripts/bootstrap_pcs_rendering_benchmarks.py
```
