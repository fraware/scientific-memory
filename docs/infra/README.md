# Infrastructure

Policy and reference documentation for CI, releases, and contributor tooling. Workflow definitions live in [.github/workflows/](../../.github/workflows/).

## Ownership

| Area | Location | Notes |
|------|----------|-------|
| CI / validation | [.github/workflows/](../../.github/workflows/) | corpus-validation, lean-ci, portal-ci, release, pcs-bench-producer, contributor-dry-run-monthly, security-sarif, mcp-contract |
| Ownership / triage | [.github/CODEOWNERS](../../.github/CODEOWNERS), [maintainers.md](../maintainers.md#community-operations-triage-labels-and-launch-cadence) | Default reviewers; labels and response targets |
| Dependency updates | [.github/dependabot.yml](../../.github/dependabot.yml) | Weekly pip, npm, and GitHub Actions updates |
| Releases | [release-policy.md](release-policy.md), [Release integrity](../contributor-playbook.md#release-integrity-gate-7) | Changelog, checksums, Sigstore signing, GitHub Release assets |
| Caching | [cache-policy.md](cache-policy.md) | Lake, uv, pnpm cache keys |
| Dev containers | [.devcontainer/](../../.devcontainer/) | Reproducible dev environment |

## Required checks before merge

- Schema and corpus validation (`validate-all`) via [`gate_engine`](../../pipeline/src/sm_pipeline/validate/gate_engine.py); optional `validate-all --report-json` for CI artifacts
- Lean build (`lake build`)
- Portal build and smoke test
- Benchmark regression when `benchmarks/baseline_thresholds.json` is present
- Schema migration notes when schemas change
- PCS release verification and producer gates when pcs-core is checked out (see [pcs/README.md](../pcs/README.md))

See workflow files under `.github/workflows/` for job names and triggers.
