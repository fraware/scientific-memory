# PCS benchmark producer

Scientific Memory is the **pcs-bench producer** for rendering evidence (`workflow_id`: `pcs.scientific_memory`).

## Output

Primary artifact (required by pcs-bench):

`benchmark_runs/<suite>/pcs_bench_ingest.v0.json`

Each ingest embeds full pcs-core v0 objects (`BenchmarkRun.v0`, `CoverageReport.v0`, `FailureLocalizationResult.v0`, `ExplainQualityReport.v0`) plus `artifact_refs` pointing at on-disk sidecars. Companion dialect JSON files remain for debugging and portal workflows.

## Prerequisites

```bash
uv sync --project pipeline --extra pcs
pip install -e ../pcs-bench
```

Sibling checkouts:

- [pcs-core](https://github.com/SentinelOps-CI/pcs-core) at `../pcs-core`
- [pcs-bench](https://github.com/fraware/pcs-bench) on `PATH`

## Commands

```bash
# LabTrust QC suite (default cases)
make pcs-bench-producer

# External reviewer packet (5 cases)
make pcs-bench-producer-external
```

Equivalent `just` targets:

```bash
just pcs-bench-producer-gate
just pcs-bench-producer-gate-external
```

Each producer run:

1. Renders benchmark cases with `--release-grade`
2. Runs `validate-pcs-bench-ingest --release-grade`
3. Runs `pcs-bench validate-ingest --release-grade`

Validate existing output:

```bash
sm-pipeline validate-pcs-bench-ingest \
  --input benchmark_runs/labtrust_rendering/pcs_bench_ingest.v0.json \
  --pcs-core ../pcs-core \
  --release-grade
```

## Release-grade requirements

With `--release-grade`, the producer fails when:

- `source_commit` is all zeros (placeholder)
- pcs-core schema validation is disabled
- `benchmark_runs`, `commands`, `logs`, or `explain_quality_reports` are empty
- Coverage metrics fall below thresholds (interpretability and query ≥ 0.95; failed-release, comparison, and staleness ≥ 0.90)
- Dialect reports or sidecar files are missing
- `artifact_refs` must cover every embedded digest
- `pcs-bench validate-ingest --release-grade` fails

## Suite registry

`benchmarks/pcs_bench/suite_registry.v0.json` lists:

| `suite_id` | Cases |
|------------|-------|
| `scientific-memory-rendering-v0` | Full `benchmarks/rendering/` (10 cases) |
| `scientific-memory-external-reviewer-v0` | `benchmarks/rendering/external_reviewer_minimal/` (5 cases) |

Ingest field reference: [bench-ingest-contract.md](bench-ingest-contract.md).

## Package for upload

```bash
python scripts/package_pcs_bench_bundle.py benchmark_runs/external_reviewer_minimal \
  --validate-pcs-core-output ../pcs-core --release-grade
```

## CI

- **corpus-validation** — producer gate when pcs-core (and optionally pcs-bench) are checked out
- **pcs-bench-producer** — always checks out pcs-core and pcs-bench; uploads ingest bundles
