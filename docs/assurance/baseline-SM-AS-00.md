# Baseline SM-AS-00

Frozen inventory at introduction of the assurance / autonomous science layer. Use this document to compare toolchain pins and pre-layer surfaces; it is not a live capability matrix.

## Git

- `HEAD` at freeze: `784140baee2589c89453243bee37ea074d0a4a2d`

## Toolchain pins (observed at freeze)

| Tool | Pin / version |
|------|----------------|
| Python | `>=3.11` (`uv.lock`); runtime `3.13.11` |
| Lean | `leanprover/lean4:v4.29.0-rc6` (`lean-toolchain`) |
| Node | `v20.10.0` |
| pnpm | `10.0.0` (`packageManager` in root / portal) |
| Lockfiles | `uv.lock`, portal `pnpm-lock.yaml` |

## Surfaces before the layer

| Need | What existed at freeze | Closed by assurance layer |
|------|------------------------|---------------------------|
| Outcome / calibration | `ResultArtifact.v0`, `RuntimeReceipt.run_outcome` | `ScientificOutcomeRecord` / `ActionCalibrationRecord` (`schemas/assurance/`) |
| Release import | PCS `pcs_import/release_manifest_importer.py` | `import-assurance-release` into `corpus/assurance/` |
| Graph | Corpus dependency graph; PCS artifact dependency graph | Append-only scientific action-chain DAG |
| CLI | `sm-pipeline` Typer app | `sm` alias; outcome/chain/export/metrics commands |
| Metrics | SPEC-12 (`docs/metrics.md`) | `autonomous-science` aggregates |
| Portal | PCS guarantee badges | `/assurance` action pages from assurance export |
| VSA / AKTA / SCOPE / PF | Not in-repo (only `formal_scope` text) | Digest-referenced via `ExternalArtifactRef` |

## PCS support (unchanged ownership)

- Docs: `docs/pcs/import-and-releases.md`
- Schemas: `schemas/pcs/` (`*.v0`)
- Release trains exercised in fixtures under `tests/pcs/fixtures/` (labtrust, tool-use, computation)

## Baseline gates

Commands expected green at freeze (and still the local pre-merge baseline). The assurance layer does not change Lean builds, corpus PCS claim digests, or SPEC-12 derived-metric semantics.

```bash
just validate
just test
just test-pcs
just lake-build
pnpm --dir portal lint && pnpm --dir portal build
```

## Design defaults frozen here

1. Assurance schemas are repo-local under `schemas/assurance/` as `*.v1.schema.json`.
2. External systems are typed refs plus optional committed snapshots; fail closed on digest, version, or lifecycle mismatch.
3. CLI: `sm` aliases `sm-pipeline`.
4. Storage: append-only `corpus/assurance/actions/<action_id>/`.
5. Outcomes and calibrations never rewrite PCS or corpus claim JSON, status, or digests.
