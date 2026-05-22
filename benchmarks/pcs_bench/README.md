# pcs-bench suite registry (Scientific Memory)

Scientific Memory publishes PCS rendering benchmark output for [pcs-bench](https://github.com/SentinelOps-CI/pcs-core) consumption.

## Registry

`suite_registry.v0.json` lists producer suites:

| `suite_id` | Cases | Purpose |
|------------|-------|---------|
| `scientific-memory-rendering-v0` | `benchmarks/rendering/` (10) | Full import/render/query/failure-evidence |
| `scientific-memory-external-reviewer-v0` | `benchmarks/rendering/external_reviewer_minimal/` (5) | Minimal reviewer packet |

## Canonical ingest

Each run writes **`pcs_bench_ingest.v0.json`** with:

- `workflow_id`: `pcs.scientific_memory`
- Embedded pcs-core objects: `benchmark_runs`, `coverage_reports`, `failure_localization_reports`, `explain_quality_reports`, `profile_coverage_reports`
- `artifact_refs`: one `BenchmarkArtifactRef.v0` per embedded explain-quality report (paths under `explain_quality_reports/`)
- `commands`, `logs`, `source_repo`, `source_commit`, `signature_or_digest`

Companion SM dialect files (`rendering_coverage_report.v0.json`, etc.) and `explain_quality_report.v0.json` (bundle) remain for debugging; pcs-bench ingests the embedded manifest.

Contract: [docs/pcs-bench-ingest.md](../../docs/pcs-bench-ingest.md).

## Run and validate

```bash
just pcs-benchmark-external-reviewer-pcs-core
just validate-external-reviewer-benchmark-pcs-core

# Full suite
just pcs-benchmark-rendering-all-pcs-core
just validate-pcs-benchmark-output-pcs-core benchmark_runs/pcs_rendering ../pcs-core

# Release-grade producer gate (pcs-bench consumable, no fixture fallback)
make pcs-bench-producer
just pcs-bench-producer-gate
just pcs-bench-producer-gate-external
```

## Package for upload

```bash
python scripts/package_pcs_bench_bundle.py benchmark_runs/external_reviewer_minimal \
  --validate-pcs-core-output ../pcs-core
```

Produces `<out>_bundle/` with ingest, v0 reports, `explain_quality_reports/`, `bench_suite_manifest.v0.json`, and contract README.

## Typed failures

`import_failed`, `render_failed`, `query_failed`, `staleness_failed`, `comparison_failed`, `formal_failed` — projected to `FailureLocalizationResult.v0` in ingest; see registry `ingest_contract.failure_kinds`.
