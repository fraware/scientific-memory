# Scientific Memory PCS benchmark producer

Scientific Memory is the **pcs-bench** producer for rendering evidence (`workflow_id`: `pcs.scientific_memory`).

## Output contract

Primary artifact (required by pcs-bench):

`benchmark_runs/<suite>/pcs_bench_ingest.v0.json`

Each ingest embeds full pcs-core v0 objects (`BenchmarkRun.v0`, `CoverageReport.v0`, `FailureLocalizationResult.v0`, `ExplainQualityReport.v0`) plus `artifact_refs` pointing at on-disk sidecars. Companion SM dialect JSON files remain for debugging and portal workflows.

## Prerequisites

Sibling checkouts (recommended):

- [pcs-core](https://github.com/SentinelOps-CI/pcs-core) at `../pcs-core`
- [pcs-bench](https://github.com/fraware/pcs-bench) installed on `PATH` (`pip install -e ../pcs-bench`)

```bash
uv sync --project pipeline --extra pcs
pip install -e ../pcs-bench   # or clone into ./pcs-bench for CI
```

## Producer commands

```bash
# Canonical producer target
make pcs-bench-producer

# External reviewer packet (5 cases, all SM metrics)
make pcs-bench-producer-external

# Validate existing output
sm-pipeline validate-pcs-bench-ingest \
  --input benchmark_runs/labtrust_rendering/pcs_bench_ingest.v0.json \
  --pcs-core ../pcs-core \
  --release-grade
```

## Release-grade gates

With `--release-grade`, the producer fails when:

- `source_commit` is all zeros (developer fixture placeholder)
- pcs-core schema validation is not enabled
- `benchmark_runs`, `commands`, `logs`, or `explain_quality_reports` are empty
- SM coverage metrics fall below thresholds (interpretability/query ≥ 0.95; failed-release/comparison/staleness ≥ 0.90)
- Dialect reports or sidecar files are missing on disk
- `artifact_refs` do not cover embedded digests
- `pcs-bench validate-ingest --release-grade` fails (including `system_admission_outcome` semantics)

## CI

- `corpus-validation` runs the producer gate when pcs-core (and optionally pcs-bench) are checked out.
- `pcs-bench-producer` workflow always checks out pcs-core + pcs-bench and uploads ingest bundles as artifacts.

## Registry

Suite definitions: `benchmarks/pcs_bench/suite_registry.v0.json`. Ingest contract details: [pcs-bench-ingest.md](pcs-bench-ingest.md).
