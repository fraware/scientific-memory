# Contributing

## Core rule

Every accepted contribution must improve at least one of:

- source traceability,
- formal correctness,
- executable alignment,
- artifact reproducibility,
- contributor usability.

## Non-negotiable requirements

- No public declaration without source linkage.
- No schema changes without migration notes.
- No generated artifact without a reproducible generator.
- No portal-only truth; portal renders from canonical corpus/manifests/export.

## Contribution paths

1. Admit a paper into the corpus.
2. Improve claim/assumption/symbol extraction.
3. Formalize mapped claims in Lean.
4. Add or extend executable kernels.
5. Improve validation/coverage/graph tooling.
6. Improve portal rendering and observability.

## Local checks

```bash
just fmt
just lint
just test
just validate
just build
```

If setup/build fails, run `just doctor` first.

**Test coverage:** Run `just test` locally. As of the current tree: **133** tests total (**107** in `pipeline/tests`, **26** in `kernels/adsorption/tests`) via the workspace `pytest` configuration (MCP contract/integration tests live in the pipeline suite). Confirm with `uv run pytest --collect-only -q`. For MCP, ensure `uv sync --extra mcp` when exercising MCP-backed tests.

**Contributor dry-run (smoke):** from repo root, `bash scripts/contributor_dry_run.sh` (or follow the same steps manually). A monthly workflow runs validate and tests on a clean runner; see `.github/workflows/contributor-dry-run-monthly.yml`.

**Pre-merge CI (local):** see [Contributor playbook – Local CI](docs/contributor-playbook.md#local-ci-checklist-green-before-merge) (validate, tests, `lake build`, portal build, benchmark).

**Public push, clean-room, branch protection, triage, launch cadence:** [docs/maintainers.md](docs/maintainers.md).

**Reuse modes (export, kernels, benchmarks):** see [Contributor playbook – Reusing Scientific Memory](docs/contributor-playbook.md#reusing-scientific-memory).

## Validation expectations

`just validate` enforces:

- schema validity,
- normalization integrity,
- provenance integrity,
- graph integrity (theorem-card dependencies + kernel/card/manifest cross-links),
- coverage integrity,
- extraction run requirement (papers with claims must have `extraction_run.json`; run `just extraction-report <paper_id>` if missing),
- claim status in allowed enum; `disputed` claims must have non-empty `review_notes`,
- migration doc updated when schemas change.

## Helpful optional commands

- `just metrics` (includes reviewer lifecycle warnings for `machine_checked_but_unreviewed` cards)
- `uv run --project pipeline python -m sm_pipeline.cli validate-all --report-json path/to/gate-report.json` (machine-readable gate report after successful validation)
- `just repo-snapshot` (regenerate [docs/status/repo-snapshot.md](docs/status/repo-snapshot.md) from manifests)
- `just check-paper-blueprint <paper_id>`
- `just export-diff-baseline` (creates snapshot baseline; see [release-policy.md](infra/release-policy.md) for naming conventions)
- `just export-portal-data`
- `just check-tooling`
- `just extract-from-source <paper_id>`
- `just build-verso`
- `just mcp-server` (requires `uv sync --extra mcp`)
- `uv run --project pipeline python -m sm_pipeline.cli batch-admit <csv_path> [--dry-run]` (admit multiple papers from CSV; `--dry-run` validates without writing)
- `uv run --project pipeline python -m sm_pipeline.cli proof-repair-proposals -o proposals.json` (human-review-only proposals; never auto-applied)

## Pull requests

Use `.github/PULL_REQUEST_TEMPLATE.md` and include:

- artifact impact,
- provenance impact,
- verification-boundary impact,
- coverage impact,
- schema impact,
- risk notes.

For review expectations, see [Contributor playbook – Reviewer guide](docs/contributor-playbook.md#reviewer-guide) (includes theorem-card reviewer lifecycle policy).
