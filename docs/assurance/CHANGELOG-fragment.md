# Assurance layer — release notes fragment

Maintainers may paste this into a tagged-release changelog.

Added the autonomous science / assurance layer:

- Schemas under `schemas/assurance/*.v1.schema.json`
- Append-only store `corpus/assurance/actions/`
- CLI (`sm` / `sm-pipeline`): `import-assurance-release`, `validate-action-chain`, `add-outcome`, `add-calibration`, `export-action-chain`, `metrics autonomous-science`, `export-assurance-portal-data`
- Portal routes under `/assurance` (from `portal/.generated/assurance-export.json`)
- Gate 6 task `assurance`; docs under `docs/assurance/`; [ADR 0014](../adr/0014-assurance-action-chain.md)

Non-claims: not live authorization or execution; no automatic claim rewrite; one failure is not definitive refutation; presence of an outcome or calibration record is not claim acceptance.
