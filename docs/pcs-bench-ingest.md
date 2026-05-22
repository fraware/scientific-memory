# pcs-bench ingest contract (Scientific Memory)

Scientific Memory exposes PCS rendering benchmarks as a **pcs-bench** producer. The canonical integration file is:

`pcs_bench_ingest.v0.json`

## Canonical ingest shape

```json
{
  "schema_version": "v0",
  "producer_id": "scientific-memory",
  "suite_id": "scientific-memory-rendering-v0",
  "workflow_id": "pcs.scientific_memory",
  "benchmark_runs": [],
  "coverage_reports": [],
  "failure_localization_reports": [],
  "explain_quality_reports": [],
  "profile_coverage_reports": [],
  "commands": [],
  "logs": [],
  "source_repo": "https://github.com/fraware/scientific-memory",
  "source_commit": "<40-char git HEAD>",
  "signature_or_digest": "sha256:..."
}
```

`benchmark_runs`, `coverage_reports`, `failure_localization_reports`, and `explain_quality_reports` embed full pcs-core v0 objects (`BenchmarkRun.v0`, `CoverageReport.v0`, `FailureLocalizationResult.v0`, `ExplainQualityReport.v0`).

**`artifact_refs` (required for pcs-bench):** one `BenchmarkArtifactRef.v0` per embedded `ExplainQualityReport.v0`, with `path` under `explain_quality_reports/<report_id>.v0.json` and `sha256` matching the embedded report digest. Companion dialect JSON files remain on disk for debugging but are not path-only ingest rows.

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
| `formal_failed` | Lean / formal-trust kernel evidence missing or incomplete |

Each event includes `responsible_component`, `repair_hint`, `artifact_path`, and optional `what_was_still_imported`.

## Release-grade producer gate

For pcs-bench producer output (not developer fixtures), use `--release-grade`:

- `source_commit` must be a real git HEAD (all-zero commits are rejected)
- pcs-core schema validation must pass
- `artifact_refs` must cover embedded explain-quality digests
- All five SM coverage metrics must be present
- Coverage adequacy: interpretability and query correctness ≥ 0.95; failed-release rendering, release comparison, and staleness detection ≥ 0.90 (skipped when `details.applicability` is `not_applicable` / `case_count` is 0)

```bash
sm-pipeline pcs-benchmark-rendering \
  --cases benchmarks/rendering/labtrust_qc_release \
  --out benchmark_runs/labtrust_rendering \
  --validate-pcs-core-output ../pcs-core \
  --release-grade

sm-pipeline validate-pcs-bench-ingest \
  --input benchmark_runs/labtrust_rendering/pcs_bench_ingest.v0.json \
  --pcs-core ../pcs-core \
  --release-grade

make pcs-bench-producer

# Cross-platform (Windows/macOS/Linux)
uv run python scripts/run_pcs_bench_producer_gate.py
uv run python scripts/run_pcs_bench_producer_gate.py \
  --cases benchmarks/rendering/external_reviewer_minimal \
  --out benchmark_runs/external_reviewer_minimal
```

## pcs-core schema validation

When a sibling [pcs-core](https://github.com/SentinelOps-CI/pcs-core) checkout is available, validate benchmark outputs against its canonical schemas:

```bash
sm-pipeline pcs-benchmark-rendering \
  --cases benchmarks/rendering/external_reviewer_minimal \
  --out benchmark_runs/external_reviewer_minimal \
  --validate-pcs-core-output ../pcs-core

python scripts/validate_pcs_benchmark_output.py \
  --out benchmark_runs/external_reviewer_minimal \
  --validate-pcs-core-output ../pcs-core
```

With `--validate-pcs-core-output`, the runner fails on any `PcsBenchIngest.v0` schema mismatch **or** pcs-core ingest semantics (including `artifact_refs` coverage of embedded explain-quality digests).

`scripts/validate_pcs_benchmark_output.py` also runs embedded-ingest structural checks and, when a sibling `pcs-core` checkout is present, applies the same pcs-core schema and semantic validation automatically.

Resolution order: CLI path, `PCS_CORE_PATH` (CI), `PCS_CORE_ROOT`, `../pcs-core`, `./pcs-core`.

When `PCS_CORE_PATH` is set (see `scripts/run_pcs_rc_ci_gate.sh`), the RC gate runs benchmark + validate with pcs-core schema checks automatically.

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
