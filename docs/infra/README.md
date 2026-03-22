# Infrastructure (Workstream F)

This directory holds policy and reference documentation for CI, release, and
contributor tooling. Implementation lives in the repo root and
`.github/workflows/`.

## Ownership

| Area | Location | Notes |
|------|----------|-------|
| CI / validation | [.github/workflows/](../../.github/workflows/) | corpus-validation, lean-ci, portal-ci, release, contributor-dry-run-monthly, security-sarif, mcp-contract |
| Ownership / triage | [.github/CODEOWNERS](../../.github/CODEOWNERS), [docs/maintainers.md](../maintainers.md#community-operations-triage-labels-and-launch-cadence) | Default reviewers; labels and response targets |
| Dependency updates | [.github/dependabot.yml](../../.github/dependabot.yml) | Weekly pip/npm/GitHub Actions PRs |
| Release process | [release-policy.md](release-policy.md), [Contributor playbook – Gate 7](../contributor-playbook.md#release-integrity-gate-7) | Changelog, checksums, Sigstore signing, GitHub Release + `release-bundle.zip` |
| Caching | [cache-policy.md](cache-policy.md) | Lake, uv, pnpm; cache keys in workflows |
| Devcontainers | [../../.devcontainer/](../../.devcontainer/) | Dev environment definition |

## Required checks (merge gates)

Before merge, the following must pass:

- Schema and corpus validation (`validate-all`), implemented by
  [`sm_pipeline.validate.gate_engine`](../../pipeline/src/sm_pipeline/validate/gate_engine.py)
  (same checks as legacy `validate_repo`; optional `validate-all --report-json`
  for CI artifacts)
- Lean build (`lake build`)
- Portal build and smoke test
- Benchmark regression (when baseline_thresholds is present)
- Migration doc check (when schemas change)

See the workflows in `.github/workflows/` for exact job names and triggers.
