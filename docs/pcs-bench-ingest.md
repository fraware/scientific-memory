# pcs-bench ingest contract (Scientific Memory)

Scientific Memory exposes PCS rendering benchmarks as a **pcs-bench** producer. The canonical integration file is:

`pcs_bench_ingest.v0.json`

## Canonical ingest shape

```json
{
  "schema_version": "v0",
  "producer_id": "scientific-memory",
  "suite_id": "scientific-memory-rendering-v0",
  "passed": true,
  "benchmark_runs": [],
  "coverage_reports": [],
  "explain_quality_reports": [],
  "query_results": [],
  "rendering_reports": [],
  "failure_summary": {},
  "source_repo": "https://github.com/fraware/scientific-memory",
  "source_commit": "<git HEAD>",
  "signature_or_digest": "sha256:..."
}
```

Registry of suites: `benchmarks/pcs_bench/suite_registry.v0.json`.

## Companion artifacts

| File | Purpose |
|------|---------|
| `benchmark_run.v0.json` | Aggregate pass/fail, metrics, typed `failure_summary` |
| `rendering_coverage_report.v0.json` | Per-case coverage with pcs-core `explain_quality_section_id` rows |
| `explain_quality_report.v0.json` | Bundle of `ExplainQualityReport.v0`-shaped per-case reports |
| `query_coverage_report.v0.json` | Query dispatch (`list_claims`, `show_claim`, `check_stale`, filters, `compare_releases`) |
| `failed_release_rendering_report.v0.json` | Failed-release evidence panels |
| `bench_suite_manifest.v0.json` | Run pointer back to registry `suite_id` |

Legacy alias: `pcs_bench_payload.json` (flattened paths; prefer ingest).

## Explain-quality sections (pcs-core)

`rendering_coverage_report.v0.json` maps interpretability rendering to:

- `provenance`
- `hashes`
- `handoffs`
- `verification`
- `formal_checks`
- `limitations`
- `lineage`
- `repair_hints`

Schemas: `schemas/pcs/benchmark/ExplainQualityReport.v0.schema.json`, `RenderingCoverageReport.v0.schema.json`.

## Typed failures

Benchmark failures are **not** collapsed into a single string. Each case emits `failure_events[]` with:

| `kind` | When |
|--------|------|
| `import_failed` | Release import or read_model finalization failed |
| `render_failed` | Section/lineage/failure-evidence rendering incomplete |
| `query_failed` | Claim index query mismatch |
| `staleness_failed` | Staleness expectation mismatch |
| `comparison_failed` | `compare_releases` subset mismatch |

Each event includes `responsible_component`, `repair_hint`, `artifact_path`, and optional `what_was_still_imported`.

## Run commands

```bash
# Full suite (10 cases)
just pcs-benchmark-rendering-all OUT=benchmark_runs/pcs_rendering

# External reviewer packet (5 cases)
just pcs-benchmark-external-reviewer OUT=benchmark_runs/external_reviewer_minimal

# Validate output (schemas + signature + pass bit)
just validate-pcs-benchmark-output benchmark_runs/pcs_rendering

# External reviewer (run + validate):
just validate-external-reviewer-benchmark

# Package directory for pcs-bench upload
python scripts/package_pcs_bench_bundle.py benchmark_runs/pcs_rendering
```

CLI equivalents:

```bash
python -m sm_pipeline.benchmark.pcs_rendering --cases benchmarks/rendering --out benchmark_runs/pcs_rendering
python -m sm_pipeline.cli pcs-benchmark-rendering --cases benchmarks/rendering/external_reviewer_minimal
```

## CI

`scripts/run_pcs_rc_ci_gate.sh` runs the external-reviewer suite and validates ingest before portal contracts complete.
