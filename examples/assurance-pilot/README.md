# Assurance pilot examples

Generated reports from the synthetic pilot fixtures. Recreate from the repo root:

```bash
uv run --project pipeline sm import-assurance-release tests/assurance/fixtures/pilot-retrospective/
uv run --project pipeline sm import-assurance-release tests/assurance/fixtures/pilot-shadow/
uv run --project pipeline sm metrics autonomous-science --out examples/assurance-pilot/metrics.json
uv run --project pipeline sm export-action-chain action-pilot-retrospective --out examples/assurance-pilot/export-retrospective/
uv run --project pipeline sm export-assurance-portal-data
```

Interpretation and non-claims: [docs/assurance/pilot-interpretation.md](../../docs/assurance/pilot-interpretation.md).

These examples are fixtures for reconstruction and metrics regression. They are not live authorization or execution records.
