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
- Arrays: `benchmark_runs`, `coverage_reports`, `explain_quality_reports`, `query_results`, `rendering_reports`
- `signature_or_digest`: canonical SHA-256 over the ingest object (excluding the digest field)

Contract: [docs/pcs-bench-ingest.md](../../docs/pcs-bench-ingest.md).

## Run and validate

```bash
just pcs-benchmark-external-reviewer
just validate-external-reviewer-benchmark

# Full suite
just pcs-benchmark-rendering-all
just validate-pcs-benchmark-output benchmark_runs/pcs_rendering

# pcs-core schema parity (when pcs-core checkout is present)
just validate-pcs-benchmark-output-pcs-core benchmark_runs/pcs_rendering ../pcs-core
```

## Package for upload

```bash
python scripts/package_pcs_bench_bundle.py benchmark_runs/external_reviewer_minimal
```

Produces `<out>_bundle/` with ingest, v0 reports, `bench_suite_manifest.v0.json`, and contract README.

## Typed failures

`import_failed`, `render_failed`, `query_failed`, `staleness_failed`, `comparison_failed`, `formal_failed` — see ingest contract `failure_kinds` in the registry.
