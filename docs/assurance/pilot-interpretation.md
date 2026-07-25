# Pilot interpretation

Synthetic **retrospective** and **shadow** pilot fixtures demonstrate the assurance layer end to end. They are fixtures, not operational production traffic.

## Locations

| Fixture | Path |
|---------|------|
| Retrospective pilot | `tests/assurance/fixtures/pilot-retrospective/` |
| Shadow pilot | `tests/assurance/fixtures/pilot-shadow/` |
| Imported corpus copies | `corpus/assurance/actions/action-pilot-retrospective/`, `action-pilot-shadow/` |
| Example reports | `examples/assurance-pilot/` |

## What the pilots show

- End-to-end import of a complete action chain
- Append-only outcome and calibration updates
- Reproducible `autonomous-science` metrics with visible exclusions
- Export and re-import through checksums

## Explicit non-claims

- Not live authorization or execution.
- One failed experiment is not definitive refutation.
- Outcomes and calibrations do not rewrite PCS or corpus claim digests or status.
- Presence of a record is not claim acceptance.

## How to run

```bash
uv run --project pipeline sm import-assurance-release tests/assurance/fixtures/pilot-retrospective/
uv run --project pipeline sm import-assurance-release tests/assurance/fixtures/pilot-shadow/
uv run --project pipeline sm metrics autonomous-science --out examples/assurance-pilot/metrics.json
uv run --project pipeline sm export-action-chain action-pilot-retrospective --out examples/assurance-pilot/export-retrospective/
uv run --project pipeline sm export-assurance-portal-data
```

Gate 6 floors and pinned metrics gold: [benchmarks/assurance/](../../benchmarks/assurance/).
