# Assurance / autonomous science layer

Durable outcome and calibration records plus an append-only scientific action-chain graph. PCS remains the portable evidence layer; assurance records reference claim IDs and digests without rewriting them.

## Scope

- Versioned schemas under `schemas/assurance/` (`*.v1.schema.json`, instance `schema_version: "v1"`).
- Append-only store under `corpus/assurance/actions/<action_id>/`.
- Import/export of assurance releases; nested PCS via existing PCS import when the release requests it.
- Portal action pages under `/assurance` (reads `portal/.generated/assurance-export.json` only).
- Metrics: `sm metrics autonomous-science` (or `just metrics-autonomous-science`).
- `just validate` / `validate-all` includes gate `assurance_corpus` (schema registry, digests, chains).
- Gate 6 task `assurance` under `benchmarks/tasks/assurance/` with floors in `benchmarks/baseline_thresholds.json`.

## Non-claims

- Not a live authorization or execution system.
- Not automatic rewriting of accepted PCS or corpus claims from outcomes or calibrations.
- One failed experiment is not definitive refutation.
- Presence of an outcome or calibration record does not mean claim acceptance.

## CLI

`sm` is an alias for `sm-pipeline` (see `pipeline/pyproject.toml`). From the repo root:

```bash
uv run --project pipeline sm import-assurance-release path/to/release/
uv run --project pipeline sm validate-action-chain <action_id>
uv run --project pipeline sm add-outcome path/to/ScientificOutcomeRecord.v1.json
uv run --project pipeline sm add-calibration path/to/ActionCalibrationRecord.v1.json
uv run --project pipeline sm export-action-chain <action_id> --out bundle/
uv run --project pipeline sm metrics autonomous-science --out metrics.json
uv run --project pipeline sm export-assurance-portal-data
```

Just recipes: `just import-assurance-release`, `just validate-action-chain`, `just export-action-chain`, `just metrics-autonomous-science`, `just export-assurance-portal-data`, `just test-assurance`.

## Docs

| Doc | Purpose |
|-----|---------|
| [baseline-SM-AS-00.md](baseline-SM-AS-00.md) | Frozen inventory at layer introduction (SM-AS-00) |
| [import.md](import.md) | Assurance release import |
| [outcomes.md](outcomes.md) | ScientificOutcomeRecord field semantics |
| [calibration.md](calibration.md) | ActionCalibrationRecord and missingness |
| [reconstruction.md](reconstruction.md) | Export and clean reconstruction |
| [pilot-interpretation.md](pilot-interpretation.md) | Pilot fixtures and interpretation |
| [CHANGELOG-fragment.md](CHANGELOG-fragment.md) | Release-notes fragment for maintainers |

## Related

- [ADR 0014](../adr/0014-assurance-action-chain.md) — ontology, immutability, ownership
- [ADR 0005](../adr/0005-schema-versioning.md) — `*.v1` vs PCS `*.v0`
- [examples/assurance-pilot/](../../examples/assurance-pilot/) — generated pilot reports
- [benchmarks/assurance/](../../benchmarks/assurance/) — Gate 6 floors and pinned metrics
- [docs/pcs/](../pcs/README.md) — PCS evidence import and portal claims
