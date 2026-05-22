# Proof-Carrying Science (PCS) in Scientific Memory

Scientific Memory is the **human-facing evidence layer** for PCS releases. It imports signed claim bundles and release manifests from [pcs-core](https://github.com/SentinelOps-CI/pcs-core), validates the release chain, stores a queryable corpus, renders claims in the portal, and publishes benchmark output for [pcs-bench](https://github.com/fraware/pcs-bench).

## Documentation map

| Guide | When to read |
|-------|----------------|
| [Import and releases](import-and-releases.md) | Import bundles or full releases, refresh fixtures, query and compare claims |
| [Benchmark producer](benchmark-producer.md) | Produce `pcs_bench_ingest.v0.json` for external consumers |
| [Bench ingest contract](bench-ingest-contract.md) | Schema fields, artifacts, typed failures, validation flags |
| [Portal rendering](portal-rendering.md) | Claim page sections, workflow profiles, formal trust display |

## Prerequisites

Sibling repositories (recommended):

- **pcs-core** at `../pcs-core` (schemas and canonical `examples/labtrust-release/`)
- **pcs-bench** on `PATH` (`pip install -e ../pcs-bench`) for producer validation

```bash
uv sync --project pipeline --extra pcs
pip install -e ../pcs-bench
```

## Quick start

### Verify a release locally

Sync fixtures from pcs-core, import the LabTrust release, run tests and portal contracts:

```bash
just refresh-pcs-release
just pcs-rc-gate          # Git Bash / Linux / macOS
just pcs-rc-gate-py       # Windows (same checks, no bash)
```

Import and open the canonical claim:

```bash
just pcs-import-release
just pcs-render-claim claim-pcs-qc-release-v0.1
```

Portal route: `/pcs/claims/claim-pcs-qc-release-v0.1`.

### Import a signed bundle only (legacy path)

When you have only `signed_science_claim_bundle.json` (no release manifest):

```bash
just pcs-import-bundle tests/pcs/fixtures/labtrust-release/signed_science_claim_bundle.json --strict --release-mode
just pcs-render-claim claim-pcs-qc-release-v0.1
```

Prefer `pcs-import-release` when `ReleaseManifest.v0.json` and `ReleaseChainValidationResult.v0.json` are available.

### Produce pcs-bench output

```bash
make pcs-bench-producer              # LabTrust QC suite
make pcs-bench-producer-external     # 5-case external reviewer packet
```

Primary artifact: `benchmark_runs/<suite>/pcs_bench_ingest.v0.json`.

## Release checklist (maintainers)

One-shot prepare (sync, corpus, verify):

```bash
just prepare-pcs-release      # Git Bash / Linux / macOS
just prepare-pcs-release-py   # Windows
```

Or step by step:

| Step | Command | What it checks |
|------|---------|----------------|
| 1 | `just refresh-pcs-release` | Schemas, release fixtures, benchmark expectations (includes bootstrap) |
| 1b | `just refresh-pcs-corpus-all` | Import all release trains into `corpus/pcs/` and portal export |
| 2 | `just pcs-rc-gate` or `just pcs-rc-gate-py` | Drift, imports, `tests/pcs`, portal contracts, external-reviewer producer |
| 3 | `make pcs-bench-producer` | LabTrust QC suite ingest (release-grade) |
| 4 | `make pcs-bench-producer-external` | External reviewer packet ingest (release-grade) |
| 5 | `python scripts/package_pcs_bench_bundle.py benchmark_runs/external_reviewer_minimal --validate-pcs-core-output ../pcs-core --release-grade` | Upload-ready bundle |

Optional full rendering suite (10 cases):

```bash
just pcs-benchmark-rendering-all-pcs-core OUT=benchmark_runs/pcs_rendering
just validate-pcs-benchmark-output-pcs-core benchmark_runs/pcs_rendering ../pcs-core
```

## Corpus layout

After import:

```text
corpus/pcs/
  claims_index.json
  claims/<claim_id>/
    signed_bundle.json
    read_model.json
    import_manifest.json
    release_manifest.json
    release_chain_validation.json
    artifact_registry.json
    handoff_manifests.json
    workflow_profile.json
    lineage.json
    scientific_memory_import_report.json
portal/.generated/pcs-export.json
```

## CI

- **corpus-validation** — PCS contract tests, release gate, producer when pcs-core is present
- **pcs-bench-producer** — Both producer targets on every push to matching paths

## Benchmark directories

- [`benchmarks/rendering/`](../../benchmarks/rendering/README.md) — Case definitions and run commands
- [`benchmarks/pcs_bench/`](../../benchmarks/pcs_bench/README.md) — Suite registry
- [`benchmarks/rendering/external_reviewer_minimal/`](../../benchmarks/rendering/external_reviewer_minimal/README.md) — Minimal 5-case packet

## Related repositories

| Repository | Role |
|------------|------|
| pcs-core | Canonical schemas, release manifests, workflow profiles |
| pcs-bench | Ingest validation and benchmark orchestration |
| Provability Fabric | Signs bundles; verification results in imports |
| LabTrust-Gym | Demo traces and runtime receipts (reference flow in import guide) |
