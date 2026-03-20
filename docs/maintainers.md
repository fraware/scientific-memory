# Maintainer handbook

Public push readiness, clean-room verification, branch protection, and post-launch community operations in one place.

| Section | Use when |
|---------|----------|
| [Public push readiness](#public-push-readiness) | Checklist and CI gates before going public |
| [Clean-room dry run](#clean-room-dry-run-maintainer) | Fresh clone / multi-OS proof |
| [Branch protection](#branch-protection-and-required-checks) | GitHub `main` rules |
| [Community operations](#community-operations-triage-labels-and-launch-cadence) | Labels, roster, first 90 days |

**Contributors:** start with [contributor-playbook.md](contributor-playbook.md). **Reuse:** [Reusing Scientific Memory](contributor-playbook.md#reusing-scientific-memory) in the same playbook.

---

## Public push readiness

Map each item to CI workflows and local commands. Keep evidence (green Actions URLs, clean-room notes) in your **team runbook** or a single tracking issue if you need an audit trail.

### Scorecard (track before launch)

| Area | Target | How to verify |
|------|--------|----------------|
| Build reproducibility | Clean clone builds on Linux, macOS, Windows (where supported) | [Clean-room dry run](#clean-room-dry-run-maintainer) (below) |
| Docs completeness | New contributor can complete one playbook without maintainer help | [Contributor playbook](contributor-playbook.md) (includes [local CI](contributor-playbook.md#local-ci-checklist-green-before-merge)) |
| Contributor trial | Dry-run script passes on a fresh runner | `bash scripts/contributor_dry_run.sh` (monthly: `.github/workflows/contributor-dry-run-monthly.yml`) |
| Security hygiene | Disclosure path clear; dependency updates automated | [SECURITY.md](../SECURITY.md), [Dependabot](../.github/dependabot.yml) |
| Release verification | Tag produces signed assets; verify script documented | [Release integrity (Gate 7)](contributor-playbook.md#release-integrity-gate-7), `scripts/verify_release_checksums.sh` |

### Required gates (must pass before public push)

These mirror merge expectations in [infra/README.md](../infra/README.md) and [CONTRIBUTING.md](../CONTRIBUTING.md).

| # | Gate | CI workflow | Local command (repo root) |
|---|------|-------------|---------------------------|
| 1 | Lean build | `lean-ci.yml` | `lake build` or `just lake-build` |
| 2 | Schema migration notes (when schemas change) | `corpus-validation.yml` (schema migration step) | `uv run python scripts/check_schema_migration.py --base main --head HEAD` |
| 3 | Corpus validation (gate engine) | `corpus-validation.yml` | `uv run --project pipeline python -m sm_pipeline.cli validate-all` or `just validate` |
| 4 | Pipeline tests | `corpus-validation.yml` | `uv run --project pipeline pytest` |
| 5 | Kernel tests | `corpus-validation.yml` | `uv run --project kernels/adsorption pytest` |
| 6 | Benchmark regression (min `tasks`, max `tasks_ceiling`) | `corpus-validation.yml`, `benchmark.yml` | `uv run --project pipeline python -m sm_pipeline.cli benchmark` or `just benchmark` |
| 7 | Portal lint and build | `portal-ci.yml` | `pnpm --dir portal lint` and `pnpm --dir portal build` |
| 8 | Portal graph smoke | `portal-ci.yml` | `node portal/scripts/smoke-graph.mjs` |
| 9 | MCP contract (optional extras) | `mcp-contract.yml` | After `uv sync --extra mcp`, run MCP tests per [Local CI checklist](contributor-playbook.md#local-ci-checklist-green-before-merge) |
| 10 | Release integrity (on tag) | `release.yml` | See [Release integrity (Gate 7)](contributor-playbook.md#release-integrity-gate-7) |

**Full local mirror (no `just`):** [Local CI checklist](contributor-playbook.md#local-ci-checklist-green-before-merge).

**With `just`:** `just check` (fmt, lint, validate, test, build).

Workflow files live under [.github/workflows/](../.github/workflows/). After the repo is on GitHub, use Actions to confirm green runs on `main`.

### Policy invariants (non-negotiable)

Aligned with [.cursor/rules/scientific-memory.mdc](../.cursor/rules/scientific-memory.mdc) and [SPEC.md](SPEC.md):

- No public theorem card without a linked claim ID.
- No claim without a valid `source_span`.
- No hand-authored portal fields that duplicate generated manifests; portal renders from canonical JSON.
- Schema changes require schema file, Python models, example fixtures, and a migration note in [Schema versioning and migration notes](contributor-playbook.md#schema-versioning-and-migration-notes).

### Sign-off

Before flipping the repo public, maintainers should:

- [ ] Confirm required CI checks are green on `main` (paste links in your runbook or release issue).
- [ ] Run [clean-room dry run](#clean-room-dry-run-maintainer) on at least one Windows and one Linux environment.
- [ ] Confirm branch protection and required checks match [Branch protection](#branch-protection-and-required-checks) below.
- [ ] Fill the **launch roster** under [Community operations](#community-operations-triage-labels-and-launch-cadence).

**Reuse (export, kernels, benchmarks):** [Reusing Scientific Memory](contributor-playbook.md#reusing-scientific-memory).

---

## Clean-room dry run (maintainer)

Use this procedure before a public push to catch environment-specific failures. Record every blocker as a GitHub issue with label `infra` or `documentation`.

### Purpose

Validate that a **fresh clone** reproduces a green build without hidden local state.

### Linux and macOS

1. Use a machine or VM without a prior clone of this repo (or use a new directory and delete any global Lean/uv caches only if you need strict isolation).
2. Install prerequisites: Git, [uv](https://docs.astral.sh/uv/), [pnpm](https://pnpm.io/), [elan](https://github.com/leanprover/elan) (Lean/Lake).
3. Clone and enter the repository.
4. Run:

   ```bash
   just doctor
   just bootstrap
   just check
   ```

5. Optional portal smoke:

   ```bash
   just export-portal-data
   just portal
   ```

6. Optional full contributor script (also run in CI monthly):

   ```bash
   bash scripts/contributor_dry_run.sh
   ```

### Windows

`just` requires Bash (Git Bash or WSL). From Git Bash in the repo root:

```bash
just doctor
just bootstrap
just check
```

If `just` is unavailable, follow the [Local CI checklist](contributor-playbook.md#local-ci-checklist-green-before-merge) step by step with PowerShell or cmd for `uv`/`pnpm`/`lake` commands.

### What to log

For each failure, capture:

- OS and shell
- Output of `just doctor` (or manual tool versions)
- Failing command and last 50 lines of output
- Whether the issue is documentation-only (fix the doc in the same PR) or code/CI

### Success criteria

- `just check` completes without error, or the equivalent commands in the [Local CI checklist](contributor-playbook.md#local-ci-checklist-green-before-merge) all pass.
- At least one maintainer has confirmed Windows and one non-Windows path.

---

## Branch protection and required checks

Configure GitHub **branch protection** on `main` (or your default branch) so external contributions cannot merge without the same gates as maintainers.

### Recommended settings

- Require a pull request before merging.
- Require approvals: at least **1** review for general changes; use judgment for urgent infra fixes.
- Require status checks to pass before merging (see below).
- Require conversation resolution before merging.
- Do not allow bypassing the above for administrators unless breaking glass for security incidents.

### Required status checks

Align names with your repository’s GitHub Actions job names. Typical jobs in this repo:

| Workflow file | Job name (verify in Actions UI) |
|---------------|--------------------------------|
| `corpus-validation.yml` | `validate-corpus` |
| `lean-ci.yml` | `build-lean` |
| `portal-ci.yml` | `build-portal` |
| `benchmark.yml` | (if separate from corpus validation) |
| `security-sarif.yml` | `ruff-sarif` (warning-first; optional as required check) |
| `mcp-contract.yml` | (optional if MCP is part of your merge bar) |

**Minimum bar** (matches engineering rules): Lean build, corpus validation, portal build, tests, benchmark regression as configured in `.github/workflows/` for your fork.

After enabling protection, open a test PR to confirm all required checks appear and block merge when failing.

### Release tags

Tagged releases (`v*`) trigger [.github/workflows/release.yml](../.github/workflows/release.yml). Restrict who can push tags or use GitHub Environments with required reviewers for production releases.

---

## Community operations: triage, labels, and launch cadence

### Maintainer response targets

- **First response** on a new issue or external PR: within **48 hours** (calendar days; adjust for holidays using the launch cadence below).
- **Named owners:** fill the **Launch roster** (below) before going public.
- **Security reports:** treat as highest priority; acknowledge within **24 hours** when possible ([SECURITY.md](../SECURITY.md)).

### Label taxonomy

| Label | Use |
|-------|-----|
| `bug` | Incorrect behavior or failing checks |
| `enhancement` | New capability or measurable improvement |
| `documentation` | Docs, playbooks, comments only |
| `good first issue` | Bounded scope, clear acceptance criteria, no deep domain expertise |
| `help wanted` | Maintainer-approved; suitable for external pickup |
| `infra` | CI, release, tooling, devcontainers |
| `corpus` | Paper admission, claims, assumptions, symbols |
| `formal` | Lean, theorem cards, mapping |
| `portal` | Next.js UI and export consumption |
| `blocked` | Waiting on upstream decision or maintainer |

Add labels in the GitHub UI to match this table; keep names stable so issue templates stay accurate.

### CODEOWNERS

Edit [.github/CODEOWNERS](../.github/CODEOWNERS) so default review requests go to active maintainers. Replace placeholder handles with your GitHub org team or usernames before relying on branch protection.

### Pull request flow

1. Contributor fills [.github/PULL_REQUEST_TEMPLATE.md](../.github/PULL_REQUEST_TEMPLATE.md).
2. CI must pass per [Public push readiness](#public-push-readiness) gates above.
3. Area owners (from CODEOWNERS or manual assignment) review for artifact and provenance impact.
4. Squash or merge per repo policy; tag releases per [Release integrity (Gate 7)](contributor-playbook.md#release-integrity-gate-7).

### Escalation

- **Scientific dispute on a claim:** involve domain reviewer; use claim `disputed` status and `review_notes` per [Reviewer guide](contributor-playbook.md#reviewer-guide).
- **Schema or SPEC ambiguity:** open an ADR under [docs/adr/](adr/README.md) or discuss in a dedicated issue before wide refactors.

### Launch roster (fill before public flip)

| Role | GitHub handle | Start date (UTC) | Notes |
|------|---------------|------------------|--------|
| Primary on-call triage | _TBD_ | | First 30 days; rotate weekly if multiple maintainers |
| Release manager | _TBD_ | | Tag + verify [Release integrity (Gate 7)](contributor-playbook.md#release-integrity-gate-7) |
| Domain reviewer (default) | _TBD_ | | Corpus / formal PRs |

Record roster assignment in your team runbook or a pinned issue if you need a paper trail.

### First 30 days (after public)

- **Daily:** Triage new issues (labels above).
- **Within 48 hours:** Acknowledge every new issue with a short comment or label.
- **Weekly:** Review open PRs; ensure CI failures are explained or fixed by contributors.
- **Weekly:** Post a short summary in Discussions (or README discussion link): merged PRs, open help-wanted items, failing trends in benchmarks if any.
- **Metrics:** Track time-to-first-response and time-to-merge for external PRs (GitHub Insights or manual spreadsheet).

### Days 31–60

- **Biweekly:** Community report: contribution count, new papers or claims admitted, benchmark delta from `benchmarks/reports/`.
- **Process:** Promote recurring contributor questions into [contributor-playbook.md](contributor-playbook.md) or FAQ.
- **Hardening:** Review Dependabot noise; tune grouping or ignore rules if needed.

### Days 61–90

- **Monthly:** Roadmap sync: update [ROADMAP.md](../ROADMAP.md) or milestone board with what shipped vs planned.
- **Quality:** Review whether theorem-card reviewer Phase 2/3 in [Contributor playbook – Theorem-card lifecycle](contributor-playbook.md#theorem-card-reviewer-lifecycle-policy) should apply to public-facing papers.
- **Sustainability:** Confirm CODEOWNERS coverage matches active maintainers; recruit backup reviewers per area.

### Success indicators

- Median time to first maintainer response under 48 hours.
- At least one external merged PR per month (adjust target by project size).
- No unexplained CI red on `main` for more than 24 hours.
- Release tags remain verifiable per [Release integrity (Gate 7)](contributor-playbook.md#release-integrity-gate-7).
