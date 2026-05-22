# pcs-bench ingest contract

Operator guide: [benchmark-producer.md](benchmark-producer.md).

The canonical integration file is `pcs_bench_ingest.v0.json`.

## Ingest shape

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

Embedded arrays contain full pcs-core v0 objects: `BenchmarkRun.v0`, `CoverageReport.v0`, `FailureLocalizationResult.v0`, `ExplainQualityReport.v0`.

### artifact_refs

pcs-bench requires one `BenchmarkArtifactRef.v0` per embedded export, with `path` under the matching sidecar directory and `sha256` equal to the embedded `signature_or_digest`.

Suite registry: `benchmarks/pcs_bench/suite_registry.v0.json`.

## Companion artifacts

| File | Purpose |
|------|---------|
| `benchmark_run.v0.json` | Aggregate pass/fail, metrics, typed `failure_summary` |
| `rendering_coverage_report.v0.json` | Per-case coverage with `explain_quality_section_id` rows |
| `explain_quality_report.v0.json` | Bundle of per-case explain-quality reports |
| `query_coverage_report.v0.json` | Query dispatch results |
| `failed_release_rendering_report.v0.json` | Failed-release evidence panels |
| `explain_quality_reports/*.v0.json` | Per-case sidecars (`artifact_refs`) |
| `coverage_reports/*.v0.json` | Per-metric sidecars (`artifact_refs`) |
| `benchmark_runs/*.v0.json` | Per-case run sidecars (multi-case suites) |
| `failure_localization_reports/*.v0.json` | Failure-localization sidecars |
| `bench_suite_manifest.v0.json` | Pointer to registry `suite_id` |

Legacy alias: `pcs_bench_payload.json` (prefer ingest).

## Explain-quality sections

`rendering_coverage_report.v0.json` maps interpretability to:

`provenance`, `hashes`, `handoffs`, `verification`, `formal_checks`, `limitations`, `lineage`, `repair_hints`

Schemas: `schemas/pcs/benchmark/ExplainQualityReport.v0.schema.json`, `RenderingCoverageReport.v0.schema.json`.

## Typed failures

Each case emits `failure_events[]` with a `kind`:

| `kind` | When |
|--------|------|
| `import_failed` | Release import or read model finalization failed |
| `render_failed` | Section, lineage, or failure-evidence rendering incomplete |
| `query_failed` | Claim index query mismatch |
| `staleness_failed` | Staleness expectation mismatch |
| `comparison_failed` | `compare_releases` subset mismatch |
| `formal_failed` | Formal trust evidence missing or incomplete |

Each event includes `responsible_component`, `repair_hint`, `artifact_path`, and optional `what_was_still_imported`.

## Release-grade validation

Use `--release-grade` for producer output (not developer placeholders):

- Real git `source_commit` (all-zero rejected)
- pcs-core schema validation passes
- `artifact_refs` cover embedded digests
- All five coverage metrics present
- Thresholds — interpretability and query ≥ 0.95; failed-release, comparison, staleness ≥ 0.90 (skipped when a case does not apply)

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
```

Cross-platform gate script:

```bash
uv run python scripts/run_pcs_bench_producer_gate.py
uv run python scripts/run_pcs_bench_producer_gate.py \
  --cases benchmarks/rendering/external_reviewer_minimal \
  --out benchmark_runs/external_reviewer_minimal
```

## pcs-core schema validation

```bash
sm-pipeline pcs-benchmark-rendering \
  --cases benchmarks/rendering/external_reviewer_minimal \
  --out benchmark_runs/external_reviewer_minimal \
  --validate-pcs-core-output ../pcs-core

python scripts/validate_pcs_benchmark_output.py \
  --out benchmark_runs/external_reviewer_minimal \
  --validate-pcs-core-output ../pcs-core
```

Resolution order is CLI path, then `PCS_CORE_PATH`, `PCS_CORE_ROOT`, `../pcs-core`, and `./pcs-core`.

The release verification gate (`scripts/run_pcs_rc_ci_gate.sh`) runs the external-reviewer suite with pcs-core validation when `PCS_CORE_PATH` is set.

## Run commands

```bash
just pcs-benchmark-rendering-all OUT=benchmark_runs/pcs_rendering
just pcs-benchmark-external-reviewer OUT=benchmark_runs/external_reviewer_minimal
just validate-pcs-benchmark-output benchmark_runs/pcs_rendering
just validate-external-reviewer-benchmark-full
python scripts/package_pcs_bench_bundle.py benchmark_runs/pcs_rendering
```

CLI:

```bash
python -m sm_pipeline.benchmark.pcs_rendering --cases benchmarks/rendering --out benchmark_runs/pcs_rendering
python -m sm_pipeline.cli pcs-benchmark-rendering --cases benchmarks/rendering/external_reviewer_minimal
```
