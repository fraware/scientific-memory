# Contributor playbook

Single entry for onboarding, local CI without `just`, reuse, review, verification boundaries, Verso, schema migrations, and Gate 7 releases. High-level rules: [CONTRIBUTING.md](../CONTRIBUTING.md). Pipeline stages and publication hooks: [pipeline-extension-points.md](pipeline-extension-points.md). Maintainer operations: [maintainers.md](maintainers.md).

## Table of contents

- [Public alpha and repository state](#public-alpha-and-repository-state)
- [Running from a release](#running-from-a-release)
- [Expectations](#expectations)
- [Contribution model](#contribution-model)
- [Domain policy](#domain-policy)
- [Role-specific tracks](#role-specific-tracks)
- [One-time setup](#one-time-setup)
- [Local CI checklist (green before merge)](#local-ci-checklist-green-before-merge)
- [Adding a paper and a claim](#adding-a-paper-and-a-claim)
- [When validation or benchmarks fail](#when-validation-or-benchmarks-fail)
- [Reviewer guide](#reviewer-guide)
- [Verification boundary](#verification-boundary)
- [Reusing Scientific Memory](#reusing-scientific-memory)
- [Verso integration (optional)](#verso-integration-optional)
- [Schema versioning and migration notes](#schema-versioning-and-migration-notes)
- [Release integrity (Gate 7)](#release-integrity-gate-7)
- [Summary](#summary)

## Public alpha and repository state

This section describes what "public alpha" means and how the repository is set up today.

- The repository is public. **Six papers** are in `corpus/index.json`: Langmuir, Freundlich, and `temkin_1941_adsorption` (chemistry/adsorption slices); `math_sum_evens` (mathematics reference slice); `chem_dilution_reference` (chemistry dilution slice with two machine-checked claims, assumptions, and symbols); `physics_kinematics_uniform` (physics kinematics slice with 15 machine-checked claims, full assumptions/symbols). Manifests currently total **62** machine-checked declarations across those papers. Adsorption kernels carry Hypothesis-based property tests plus pytest numeric witnesses in CI.
- Contributors can add a claim, run the pipeline, and pass CI. All seven CI gates are in place (Lean build, schema validation including normalization, extraction_run for papers with claims, and kernel/theorem-card referential integrity, provenance, coverage, portal build, benchmark regression with proof-success snapshot, runtime budgets, minimum thresholds under `tasks`, and **`tasks_ceiling`** (e.g. source-span alignment error rate on `tasks.gold`), release integrity with checksums and Sigstore keyless signing). Validation is centralized in [`sm_pipeline.validate.gate_engine`](../pipeline/src/sm_pipeline/validate/gate_engine.py); use `validate-all --report-json` for a machine-readable report after a successful run. **Tests:** **133** tests total (**107** in `pipeline/tests`, **26** in `kernels/adsorption/tests`; see `just test` or `uv run pytest --collect-only -q`). Ruff on pipeline. Run `just doctor` if setup fails; use `just lake-build` or `just lake-build-verbose LOG=file.log` for Lean diagnostics.
- Release and tagging are the single source of truth for "what is released." No separate artifact tarball is required for the alpha; cloning at a release tag is the canonical way to obtain a reproducible snapshot. Gate 7 is documented under [Release integrity (Gate 7)](#release-integrity-gate-7) in this playbook.
- Maintainers preparing to go public should follow [maintainers.md](maintainers.md).

### Quick start (developers)

From the repo root:

1. **Clone and bootstrap**

   ```bash
   git clone <repo-url>
   cd scientific-memory
   just bootstrap
   ```

2. **Build**

   ```bash
   just build
   ```

   This runs the Lean build, portal build, and pipeline/kernel tests. Ensure all pass before changing corpus or formal code.

3. **Run the portal locally**

   ```bash
   just portal
   ```

   Open the URL shown (e.g. http://localhost:3000) to browse papers, claims, theorem cards, kernels, the coverage dashboard, search, and the diff page (baseline vs current corpus). Run `just export-diff-baseline` before a release to refresh the diff baseline. Run `just metrics` for derived metrics (median intake, dependency, symbol conflict, proof completion, axiom count, research-value, source-span alignment, normalization visibility, assumption-suggestions, dimension-visibility, dimension-suggestions). Optional: `just check-tooling` (pandoc), `just extract-from-source <paper_id>` (output includes macro_context from preamble), `just build-verso`, `just mcp-server` (tools: list_declarations_for_paper, list_declarations_in_file, get_dependency_graph_for_declaration; requires `uv sync --extra mcp`).

4. **Contributing**

   Use [Adding a paper and a claim](#adding-a-paper-and-a-claim) below. See [CONTRIBUTING.md](../CONTRIBUTING.md) and [Reviewer guide](#reviewer-guide) for workflow and review expectations.

## Running from a release

To use a specific released version:

- **Clone at tag:** `git clone --branch v0.1.0 <repo-url>` (or after clone, `git checkout v0.1.0`). Then run `just bootstrap` and `just build` as above.
- Release tags trigger a workflow that publishes a **GitHub Release** with changelog, checksums, Sigstore signature files, and `release-bundle.zip` (full `dist/`). Cloning at the tag remains the primary developer path; release assets support deterministic verification (see [Release integrity (Gate 7)](#release-integrity-gate-7)).

## Expectations

- The first success criterion is one full paper artifact (claims, formalization, theorem cards, manifest, portal). Platform completeness is secondary.
- Schema and corpus changes must follow [Schema versioning and migration notes](#schema-versioning-and-migration-notes) and the rules in [SPEC](SPEC.md); no merge without passing CI.

## Contribution model

Contributions flow through:

1. **Paper admission**: Add a paper directory under corpus/papers with metadata and (initially empty or stub) claims/assumptions/symbols.
2. **Extraction**: Run extraction pipelines to populate claims, assumptions, symbols from source-adjacent inputs.
3. **Formalization**: Add Lean declarations under formal/ScientificMemory, linked via mapping.json and theorem cards.
4. **Kernels**: Add or extend executable kernels with declared contracts and linked theorem cards.
5. **Validation**: All changes must pass the unified gate sequence (`sm_pipeline.validate.gate_engine`): schema validation, normalization (unique IDs, resolved edges), provenance, graph integrity (theorem-card and kernel linkage), coverage, extraction_run requirement (papers with claims must have `extraction_run.json`), claim status and disputed-review_notes rules, migration doc check when schemas change, and non-blocking snapshot-quality warnings. Optional machine-readable output: `validate-all --report-json <path>`.
6. **Publish**: Manifests and portal data are generated from corpus and formal artifacts only. Portal export uses `portal_read_model.build_portal_bundle` (`just export-portal-data`). Regenerate [status/repo-snapshot.md](status/repo-snapshot.md) after corpus changes: `just repo-snapshot`.

Optional: run `just metrics` for derived metrics (includes normalization-policy report, reviewer_report, assumption-suggestions, dimension-visibility, dimension-suggestions); optional policy file `benchmarks/normalization_policy.json`; `just check-paper-blueprint <paper_id>`; `just export-diff-baseline` (or `sm-pipeline export-diff-baseline --baseline-id <id> --title ... --narrative ...`); `just check-tooling` (pandoc); `just extract-from-source <paper_id>`; `just build-verso`; `just mcp-server` (requires `uv sync --extra mcp`); proof-repair proposals via `sm-pipeline proof-repair-proposals -o path` (human-review only); human-gated `proof-repair-apply` after review (formal tree only; never in CI); bulk skeleton admission via `sm-pipeline batch-admit` (see [paper-intake](paper-intake.md)); stage-shaped automation via `sm_pipeline.pipeline_orchestrator` for SPEC 8.x steps where applicable.

No hand-authored portal truth; no public theorem card without a linked claim ID.

## Domain policy

Domains are used for taxonomy and routing. Each paper has a single `domain` in metadata (schema enum includes **chemistry**, **mathematics**, **physics**, **probability**, **control**, **quantum_information**, **other**). Namespaces under `formal/ScientificMemory` are organized by domain (e.g. `Chemistry.Adsorption`, `Mathematics.SumEvens`). Cross-domain references are allowed but should be explicit in provenance and docs. When you introduce a new domain value, extend `schemas/paper.schema.json`, the pipeline `Paper` model, add a migration note under [Schema versioning and migration notes](#schema-versioning-and-migration-notes), and extend this section if policy needs documenting.

## Role-specific tracks

Follow a role-specific path for a focused workflow and gate checklist:

| Role | Playbook | Use when |
|------|----------|----------|
| **Formalizer** | [playbooks/formalizer.md](playbooks/formalizer.md) | Adding or extending Lean formalizations and linking to claims. |
| **Reviewer** | [playbooks/reviewer.md](playbooks/reviewer.md) | Reviewing PRs; verifying gates and artifact impact. |
| **Domain expander** | [playbooks/domain-expander.md](playbooks/domain-expander.md) | Adding a paper in a new domain (e.g. first mathematics or physics paper). |
| **Release manager** | [playbooks/release-manager.md](playbooks/release-manager.md) | Cutting a release; tagging, signing, and publishing artifacts. |

Each playbook includes a gate checklist, end-to-end path, and failure troubleshooting so you can complete the workflow without maintainer help.

## One-time setup

From the repo root:

```bash
git clone <repo-url>
cd scientific-memory
just bootstrap
just build
just portal
```

In another terminal, run validation and benchmarks to confirm the corpus and pipeline are healthy:

```bash
just validate-corpus
just benchmark-smoke
```

If any of these fail, run `just doctor` to verify tool versions (uv, pnpm, lean, lake). If `lake` or `lean` is not found, ensure elan is installed and the repo is your working directory. For Lean build diagnostics use `just lake-build-verbose LOG=lake-build.log` to capture full output. Then fix the reported errors (schema, provenance, coverage, or benchmark thresholds) before changing the corpus.

## Local CI checklist (green before merge)

Run from the repository root. Mirrors the main gates without requiring `just` (which needs Bash on Windows).

### 1. Validate corpus and schemas

```bash
uv run --project pipeline python -m sm_pipeline.cli validate-all
```

Optional machine-readable gate report (after success):

```bash
uv run --project pipeline python -m sm_pipeline.cli validate-all --report-json /tmp/gate-report.json
```

Or: `just validate` (Bash).

Regenerate [status/repo-snapshot.md](status/repo-snapshot.md): `just repo-snapshot` (requires `uv`; Bash via `just`).

### 2. Tests

Pipeline and kernel unit tests:

```bash
uv run --project pipeline pytest
uv run --project kernels/adsorption pytest
```

MCP contract tests (requires `uv sync --extra mcp`):

```bash
uv run --project pipeline pytest pipeline/tests/test_mcp_server_contract.py pipeline/tests/test_mcp_server_data_paths.py
```

Optional smoke (Unix): `bash tests/smoke/test_repo_bootstrap.sh` (also run via `just test`).

**Current status:** Run `pytest` locally for current counts; pipeline and kernel suites include gate-engine, portal read-model, and orchestrator tests.

### 3. Lean and portal

```bash
lake build
pnpm --dir portal lint
pnpm --dir portal build
```

Or: `just build` (runs Lean, portal build, then both pytest suites).

**Note:** Portal lint checks Prettier formatting and TypeScript types. Run `pnpm --dir portal format` to auto-fix formatting issues.

### 4. Benchmark regression (Gate 6)

```bash
uv run --project pipeline python -m sm_pipeline.cli benchmark
```

Fails if metrics fall below minima in `tasks` or exceed maxima in `tasks_ceiling` (e.g. `tasks_ceiling.gold.source_span_alignment_error_rate`). Raise or lower thresholds only when the team agrees metrics should tighten.

### 5. Code quality checks

```bash
uv run --project pipeline ruff check pipeline kernels kernels/conformance scripts tests
```

Ruff checks for code quality issues (unused imports, variables, etc.). All checks should pass before merge.

### 6. Refresh artifacts after corpus or formal edits

```bash
uv run --project pipeline python -m sm_pipeline.cli publish --paper-id <paper_id>
uv run --project pipeline python -m sm_pipeline.cli export-portal-data
pnpm --dir portal build
```

`portal build` regenerates `portal/public/search-index.json` when configured in `portal/package.json`.

**See also:** [SPEC.md](SPEC.md), [ROADMAP.md](../ROADMAP.md), [CONTRIBUTING.md](../CONTRIBUTING.md).

## Adding a paper and a claim

1. **Admit the paper**

   ```bash
   just add-paper langmuir_1918_adsorption
   ```

   This creates `corpus/papers/langmuir_1918_adsorption/` with initial `metadata.json`, `claims.json`, `assumptions.json`, `symbols.json`, `mapping.json`, and `manifest.json`. Use a short, stable `PAPER_ID` (e.g. `author_year_topic`). When adding a paper, if you have a DOI or arXiv ID, set `metadata.source.doi` or `metadata.source.arxiv_id` in the paper's metadata.

2. **Extract claims (scaffold)**

   ```bash
   just extract-claims langmuir_1918_adsorption
   ```

   If `claims.json` is missing or empty, this writes a single placeholder claim. Otherwise it leaves the file unchanged.

3. **Scaffold formal mapping**

   ```bash
   just scaffold-formal langmuir_1918_adsorption
   ```

   This ensures `mapping.json` exists with a valid `paper_id`, `namespace`, and `claim_to_decl` map. Existing entries are preserved.

4. **Edit corpus and Lean**

   - Edit `corpus/papers/<PAPER_ID>/claims.json`: set `source_span`, `informal_text`, `claim_type`, `status`, and (optionally) `linked_assumptions`, `linked_symbols`.
   - Edit `corpus/papers/<PAPER_ID>/assumptions.json` and `symbols.json` as needed.
   - Edit `corpus/papers/<PAPER_ID>/mapping.json`: add entries in `claim_to_decl` mapping each claim ID to the corresponding Lean declaration name.
   - Add or update Lean code under `formal/` so that the declarations compile and (if applicable) proofs are machine-checked.

5. **Check the paper**

   ```bash
   just check-paper langmuir_1918_adsorption
   ```

   Optionally, compare the paper's blueprint to `mapping.json`: `just check-paper-blueprint langmuir_1918_adsorption`. Reports claim IDs in the blueprint that are missing or differ in mapping (mapping is authoritative for the build).

   This runs full corpus validation (schema, normalization, provenance, coverage). Fix any reported errors:
   - **Schema:** Ensure every required field is present and types match the schemas in `schemas/`.
   - **Normalization:** No duplicate claim/assumption/symbol IDs per paper; every `linked_assumptions` and `linked_symbols` entry must resolve to an existing ID.
   - **Provenance:** Every claim must have a `source_span`; every declaration in the manifest must be linked from a claim via the mapping.
   - **Coverage:** Regenerate the manifest so that `coverage_metrics` match the current claims (do not edit `manifest.json` by hand for coverage).

6. **Publish artifacts**

   ```bash
   just publish-artifacts langmuir_1918_adsorption
   ```

   This regenerates `theorem_cards.json` and `manifest.json` (including `dependency_graph` from theorem cards’ `dependency_ids`, `generated_pages`, and `kernel_index` when applicable).

7. **Run full check**

   ```bash
   just check
   ```

   This runs format, lint, validate, test, and build (Lean, portal, pipeline, kernels). All must pass before opening a PR.

## When validation or benchmarks fail

- **Schema validation:** Check the failing file against the JSON schema in `schemas/`. Use the pipeline’s `validate-all` output to see which file and field failed. After a successful run, `validate-all --report-json <path>` writes the ordered gate checklist from [`gate_engine`](../pipeline/src/sm_pipeline/validate/gate_engine.py).
- **Normalization:** No duplicate claim/assumption/symbol IDs per paper; every `linked_assumptions` and `linked_symbols` reference must resolve to an existing ID in that paper.
- **Provenance (Gate 3):** Add or fix `source_span` on claims; ensure every declaration in the manifest is reachable from some claim via `mapping.json`’s `claim_to_decl`.
- **Coverage (Gate 4):** Run `just publish-artifacts <paper_id>` so that `manifest.json`’s `coverage_metrics` are recomputed from the current claims. Do not edit `coverage_metrics` manually.
- **Benchmark regression:** If extraction/mapping/theorem_cards/gold metrics fall below minima in `tasks` or above maxima in `tasks_ceiling` (e.g. source-span alignment error rate), either fix corpus/gold drift or adjust `benchmarks/baseline_thresholds.json` (with team agreement).

## Reviewer guide

How to review a pull request so artifact impact, provenance, verification boundaries, and coverage are explicit and checks pass.

### Claim status lifecycle and required audit fields

**Allowed statuses** (must match `common.schema.json`): `unparsed`, `parsed`, `mapped`, `stubbed`, `compiles_with_sorries`, `machine_checked`, `linked_to_kernel`, `disputed`, `superseded`.

**Required audit fields:**

- **disputed:** When a claim has `status: "disputed"`, `review_notes` must be non-empty (justification for the dispute). Enforced by `just validate` (gate engine in `sm_pipeline.validate.gate_engine`); failure blocks merge.

**Lifecycle:** Typical flow is forward (unparsed to parsed to mapped to machine_checked). `disputed` is a side state requiring human resolution; once resolved, move the claim back to an appropriate status and retain or clear `review_notes` as needed. Invalid status values (not in the allowed set) are rejected by validation.

A machine-readable reviewer report (claims by status, disputed with/without notes, invalid status list) is available via `just metrics` (included in full report) or the pipeline `compute_reviewer_report` API.

### Theorem card `reviewer_status`

Theorem cards carry required `reviewer_status` (schema: `theorem_card.schema.json`): `unreviewed`, `reviewed`, `accepted`, or `blocked`. **Rules enforced by validation:**

- Values must be one of the schema enum entries.
- `blocked` requires non-empty `notes` on the card.
- `accepted` requires `proof_status: "machine_checked"`.

Publishing merges prior `reviewer_status` and `notes` so human edits are not dropped on regenerate. After formal review, set `accepted` or `reviewed` on the card JSON (or rely on publish defaults derived from claim `proof_status`). Cross-paper disputed-formalization counts appear under `just metrics --research-value` as `disputed_claims_with_formal_targets` (claim-level). Theorem-card reviewer queue counts (`blocked`, `unreviewed`, `reviewed`, `accepted`) are emitted by `just metrics` under `reviewer_status` and surfaced on the portal dashboard.

### Theorem-card reviewer lifecycle policy

SPEC 0.2: this is the **intended** human workflow for `reviewer_status` on theorem cards. Enforcement is staged: metrics warnings first; stricter CI or merge rules are optional and must be adopted explicitly by maintainers.

**States**

| Status | Meaning |
|--------|---------|
| `unreviewed` | Card generated or updated; no human reviewer sign-off. |
| `reviewed` | A reviewer inspected mapping, proof boundary, and claim link; not necessarily final. |
| `accepted` | Approved for publication scope; **requires** `proof_status: "machine_checked"` (validated). |
| `blocked` | Do not treat as trusted; **requires** non-empty `notes` (validated). |

**Allowed transitions**

- `unreviewed` → `reviewed` → `accepted` (typical forward path for machine-checked cards).
- `unreviewed` → `blocked` when formalization or mapping is disputed.
- `blocked` → `reviewed` or `accepted` after resolution (clear or update `notes`).
- `reviewed` → `unreviewed` is allowed only for **regeneration hygiene** (e.g. republish reset); document in the PR why status was pulled back.
- `accepted` → `reviewed` or `unreviewed` is a **conscious rollback** (e.g. proof regression); fix proof or status in the same change set.

Schema and `just validate` (via the [gate engine](../pipeline/src/sm_pipeline/validate/gate_engine.py)) already enforce: valid enum, `blocked` + notes, `accepted` + machine-checked.

**Staged enforcement (warn to block)**

1. **Phase 1 (current):** `just metrics` includes `reviewer_status` counts and emits a **warning** when any card is `machine_checked` but still `unreviewed` (see `reviewer_status.machine_checked_but_unreviewed` in the JSON report). This does not fail CI.
2. **Phase 2 (optional):** Treat a high count of `unreviewed` machine-checked cards as a **merge recommendation** (branch protection or reviewer checklist).
3. **Phase 3 (optional):** CI fails if papers in a named allowlist have public-facing cards not in `accepted` or `reviewed`. Requires maintaining that list and excluding WIP papers.

**Relation to claim status:** Claim-level `status` and `disputed` rules are in [Claim status lifecycle and required audit fields](#claim-status-lifecycle-and-required-audit-fields) above. Theorem-card reviewer status is **orthogonal**: it tracks human trust in the card bundle, not only Lean compilation.

### What to verify

Every PR should clearly state:

- **Artifact impact**: papers, claim bundles, declarations, kernels, or portal routes changed.
- **Provenance impact**: new/edited claims have source spans; declarations are mapped from claims.
- **Verification-boundary impact**: proof status, axioms/sorry usage, kernel witness status, reviewer status.
- **Coverage impact**: before/after metrics where corpus/formal changes occur.
- **Schema impact**: modified schemas and migration notes if needed.
- **Risk impact**: new risks introduced (or explicitly none).

### Required checks

Before approval, ensure these pass:

- `just validate`
- `just test`
- `just build`

If local setup/checks fail, run `just doctor` to validate toolchain availability.

### What `just validate` must guarantee

- schema validation (including theorem cards and kernels when present),
- normalization integrity (unique IDs and resolved links),
- provenance integrity,
- graph integrity:
  - theorem-card dependency IDs resolve,
  - kernel linked theorem cards resolve,
  - theorem-card executable links resolve to kernels,
  - manifest kernel index resolves to kernels,
- coverage integrity,
- extraction run requirement: papers with non-empty claims have `extraction_run.json` (run `just extraction-report <paper_id>` if missing),
- migration note in [Schema versioning and migration notes](#schema-versioning-and-migration-notes) in this playbook when schemas change.

### Red flags

- Claim added/changed without `source_span`.
- Declaration added/changed but not represented in paper mapping.
- Hand-edited manifest coverage metrics.
- Dangling theorem-card or kernel references.
- Schema changes without migration notes.
- Generated artifacts changed without clear generator command.
- Paper has claims but no `extraction_run.json`.

### Reviewer notes

Use PR comments to separate blocking issues from follow-up suggestions.

## Verification boundary

Every formal declaration and executable kernel has a verification boundary:

- **fully_machine_checked**: Full machine proof, no axioms.
- **machine_checked_plus_axioms**: Proof complete modulo stated axioms.
- **numerically_witnessed**: Checked by tests/simulations only.
- **schema_valid_only**: Structure validated, no semantic check.
- **human_review_only**: Human-verified only.

The boundary is stored in theorem cards and kernel manifests. The portal and reports surface it so readers know what is guaranteed.

### Proof-repair proposals (human-review boundary)

The proof-repair workflow generates **proposal artifacts** only; it never modifies the corpus. Run:

```bash
uv run --project pipeline python -m sm_pipeline.cli proof-repair-proposals -o path/to/proposals.json
uv run --project pipeline python -m sm_pipeline.cli proof-repair-proposals --paper-id PAPER_ID -o out.json
```

Output conforms to `schemas/proof_repair_proposal.schema.json`. Every proposal has `verification_boundary: "human_review_only"`. Apply any change to the formal tree or theorem cards only after human review; the pipeline does not auto-apply repair proposals in CI.

### Proof-repair apply (human-gated, formal tree only)

After reviewing proposals, a maintainer may apply an auditable bundle of find/replace patches **only under `formal/`** using:

```bash
uv run --project pipeline python -m sm_pipeline.cli proof-repair-apply --bundle path/to/bundle.json --i-understand-human-reviewed
```

The bundle schema is `schemas/proof_repair_apply_bundle.schema.json`. CI must never run `proof-repair-apply`. Regenerate theorem cards and manifests (`just publish-artifacts`) after Lean edits; run `just validate` and `just lake-build` before merge.

## Reusing Scientific Memory

This section describes **supported** ways third parties can reuse the repository and add value. For extending the pipeline in-tree, see [pipeline-extension-points.md](pipeline-extension-points.md).

### 1. Consume the portal export bundle (minimal Lean)

**Use case:** Build a custom UI, analytics, or tooling that reads the same JSON the portal uses.

1. Clone the repository.
2. Install **uv** (and Python toolchain) per [Local CI checklist](#local-ci-checklist-green-before-merge). You do **not** need pnpm or Lean **only if** you obtain `corpus-export.json` from a release artifact or another machine that ran export.
3. From repo root, generate the bundle:

   ```bash
   uv sync --all-packages
   uv run --project pipeline python -m sm_pipeline.cli export-portal-data
   ```

4. Read **`portal/.generated/corpus-export.json`**. Shape is defined only by `build_portal_bundle` in [`pipeline/src/sm_pipeline/publish/portal_read_model.py`](../pipeline/src/sm_pipeline/publish/portal_read_model.py) (`sm_pipeline.publish.portal_read_model`).

**Version field:** `version` in the JSON matches `PORTAL_BUNDLE_VERSION` in that module; treat unknown versions as potentially incompatible.

**Also useful:** JSON Schemas under [`schemas/`](../schemas/) and examples under `schemas/examples/` for contract-stable parsing.

### 2. Fork for a new paper or domain

**Use case:** Admit papers, formalize in Lean, publish manifests, and ship through the portal using the full monorepo.

Follow this playbook ([Adding a paper and a claim](#adding-a-paper-and-a-claim)), [paper-intake.md](paper-intake.md), and [Domain policy](#domain-policy). All merge paths expect **gate engine** green and (for substantive changes) portal + Lean CI parity.

### 3. Executable kernels

**Use case:** Add numerical or computational witnesses linked to theorem cards.

- Existing pattern: [`kernels/adsorption/`](../kernels/adsorption/) with tests depending on workspace package [`kernels/conformance/`](../kernels/conformance/).
- New kernel **family:** add `kernels/<family>/` with its own `pyproject.toml`, depend on `kernel-conformance`, register in `corpus/kernels.json`, and ensure CI runs your pytest (extend [corpus-validation workflow](../.github/workflows/corpus-validation.yml) or document a separate workflow if you split jobs).

### 4. `sm_pipeline` outside this monorepo (expectations)

**Today the supported path is “run from repo root”** with `uv run --project pipeline ...`: paths assume `corpus/`, `schemas/`, and `formal/` layout.

A **time-boxed spike** to reuse `sm_pipeline` as a library in another repo would need:

- vendoring or `uv` path dependency on `pipeline/`;
- explicit `repo_root` arguments (many CLIs use `Path(".")`);
- copies of or symlinks to `schemas/` and corpus inputs.

Document findings in a discussion or ADR if you pursue this; upstream may later split a publishable package if demand is clear.

### 5. Research and benchmarks (adding value without UI)

**Use case:** Extraction quality, proof-completion trends, gold labels.

- **Gold:** `benchmarks/gold/<paper_id>/` and `just scaffold-gold` ([metrics.md](metrics.md)).
- **Regression:** `just benchmark` and `benchmarks/baseline_thresholds.json` (min `tasks`, max `tasks_ceiling`).
- **Derived metrics:** `just metrics` for reviewer queues, symbol conflicts, dependency reuse, etc.

External evaluators can cite frozen **release tags** and `dist/` checksums per [Release integrity (Gate 7)](#release-integrity-gate-7).

### Unsupported / out of scope

- Hand-edited `manifest.json` coverage or portal-only “truth” (violates project invariants).
- Claiming formal support in kernel manifests without linked theorem cards ([engineering rules](../.cursor/rules/scientific-memory.mdc)).

**See also:** [maintainers.md](maintainers.md).

## Verso integration (optional)

SPEC Section 1 lists "optional Verso-backed long-form technical docs." This section defines the integration contract and current setup.

### What Verso is

Verso is used by the Lean project for long-form documentation (e.g. The Hitchhiker's Guide to Logical Verification). It can render Markdown and Lean code blocks with cross-references. See [SPEC.md](SPEC.md) and [ROADMAP.md](../ROADMAP.md). Human-oriented Markdown under [docs/verso/](verso/) complements the Lean manual sources under [scripts/verso/](../scripts/verso/).

### Current Lake setup

- **Dependency:** Verso is listed in [lakefile.toml](../lakefile.toml) with `rev = "v4.29.0-rc6"`, aligned with [lean-toolchain](../lean-toolchain) (`leanprover/lean4:v4.29.0-rc6`). Do not pin Verso to a tag that does not match the toolchain.
- **Build:** [scripts/verso/Main.lean](../scripts/verso/Main.lean) defines the `generate-site` executable and calls Verso's manual generator. The manual content is authored in Lean (e.g. [ScientificMemoryVerso.lean](../scripts/verso/ScientificMemoryVerso.lean)), not only in `docs/verso/*.md`.
- **Output:** From repo root, run `just build-verso` or `lake exe generate-site`. HTML is emitted to `docs/verso/_build/` (gitignored; see [generated-artifacts.md](generated-artifacts.md)).
- **CI:** The Verso site build is **not** a required CI gate; corpus validation and the main `lake build` for `formal/` remain the merge bar.

#### Toolchain upgrades

Verso tags follow Lean releases (see [Verso tags](https://github.com/leanprover/verso/tags)). When you change `lean-toolchain`, update the `rev` for **both** `verso` and `mathlib` in `lakefile.toml`, then run `lake update` and `lake build`.

#### Remaining product work

Treat Verso as **partially** integrated: the Lake dependency and `generate-site` path exist, but richer manual content, stable URLs for portal links (e.g. optional `theorem_card.verso_url`), and optional CI for the static site are still incremental. Track scope in [ROADMAP.md](../ROADMAP.md).

#### Network and reservoir requirements

A working network connection to the Lean package reservoir is required for `lake update`. Lake fetches pre-built dependencies (e.g. mathlib) from the reservoir; without access, `lake update` fails.

**Common failure:** If you see `external command 'curl' exited with code 35` and `leanprover-community/mathlib: Reservoir lookup failed`, this usually indicates a TLS or network problem (e.g. unreachable host, corporate proxy, or firewall blocking the reservoir). Resolve by running `lake update` (and `lake build`) in an environment with outbound HTTPS to the reservoir, or retry when the network is available; transient reservoir failures can sometimes be overcome with a retry.

**Workaround when the reservoir is unreachable:** This repo configures mathlib via **git** instead of the reservoir ([lakefile.toml](../lakefile.toml): `[[require]] name = "mathlib" git = "..." rev = "v4.29.0-rc6"`). Lake then clones mathlib4 from GitHub, so `lake update` does not need the Lean reservoir. The first run may take longer (cloning and, if used, building cache). If you prefer to use the reservoir when it is reachable, you can switch back to `scope = "leanprover-community"` and remove the `git`/`rev` fields for mathlib.

**Windows: certificate revocation check (curl 35 CRYPT_E_NO_REVOCATION_CHECK):** If `lake update` fails during mathlib's post-update hook with `CRYPT_E_NO_REVOCATION_CHECK` (e.g. when fetching the Lean cache/leantar), the Schannel SSL backend cannot verify revocation. Two options:

1. **Skip the cache fetch:** Set `MATHLIB_NO_CACHE_ON_UPDATE=1` before running `lake update`. The update will complete without downloading pre-built cache; the first `lake build` will be slower (mathlib compiles from source). On Windows (PowerShell): `$env:MATHLIB_NO_CACHE_ON_UPDATE="1"; lake update`. On Windows (cmd): `set MATHLIB_NO_CACHE_ON_UPDATE=1` then `lake update`. From Git Bash, if `just lake-update-no-cache` reports "lake: command not found", run `MATHLIB_NO_CACHE_ON_UPDATE=1 lake update` in the same terminal where `lake` works (e.g. where elan is in PATH).
2. **Allow curl to skip revocation:** Create or edit `%USERPROFILE%\.curlrc` and add the line `--ssl-no-revoke`. Then run `lake update` again. This reduces revocation checking only for curl; use only if your environment requires it.

**Disk space:** Building the `generate-site` executable compiles Verso and its dependencies (SubVerso, VersoManual, etc.) under `.lake/packages/`. The first `lake exe generate-site` can need several hundred MB of free space. If you see `resource exhausted (error code: 28, no space left on device)` or clang "No space left on device", free disk space (or move the repo to a drive with more space), then run `lake exe generate-site` again. `lake build` alone does not build the exe, so it can succeed even when the exe build would run out of space.

### Verso integration contract (product)

1. **Input:** Verso-compatible sources under `scripts/verso/` (Lean manual) and optional Markdown under `docs/verso/` for contributors.
2. **Build:** `just build-verso` or `lake exe generate-site` produces static HTML under `docs/verso/_build/`.
3. **Output:** When published (local preview, separate hosting, or future portal links), long-form pages should be addressable in a stable way so paper or theorem-card views can deep-link.
4. **No schema change:** Verso content is supplementary. Corpus, manifests, and portal JSON remain the source of truth. Optional metadata (e.g. `theorem_card.verso_url`) may be added later without changing the proof pipeline contract.
5. **CI (optional):** A workflow may build or link-check the site; it must not block corpus validation or the main Lean library build.

### Verso checklist (extend or upgrade)

1. After any `lean-toolchain` bump, align `verso` and `mathlib` revisions in `lakefile.toml` and run `lake update` / `lake build`.
2. Extend the manual in `scripts/verso/` (and keep `docs/verso/` in sync for human readers if desired).
3. Run `just build-verso` and confirm `docs/verso/_build/` contains the expected HTML.
4. When portal linking or optional CI is added, document URLs and workflows here and in [ROADMAP.md](../ROADMAP.md).

**References:** SPEC Section 1; [ADR index](adr/README.md) (no Verso ADR yet).

## Schema versioning and migration notes

Canonical schemas live in `schemas/*.schema.json`. They use JSON Schema draft 2020-12 and `$id` for resolution.

- **Backward compatibility**: New optional properties and new enum values are allowed; removing or renaming properties requires a new major version and migration.
- **Migration**: When changing a schema, update the schema file, the corresponding Pydantic model in the pipeline, example fixtures in schemas/examples/, and add a dated entry under **Migration notes** below.

**SPEC 8.3 Normalization:** Validation (in `validate_repo`) ensures no duplicate claim/assumption/symbol IDs per paper and that every claim's `linked_assumptions` and `linked_symbols` resolve to existing IDs. Visibility tooling: `just metrics --normalization-report` (cross-paper duplicate normalized_name; report includes `suggest_merge` for human triage), `just metrics --normalization-visibility` (symbols with role_unclear, claims without linked_assumptions), `just metrics --assumption-suggestions` (candidate assumptions for claims with none; text overlap), `just metrics --dimension-visibility` (symbols with vs without dimensional_metadata), `just metrics --dimension-suggestions` (heuristic suggested unit/dimension from kernels and symbol names; human triage only, no auto-edit). Full automation (auto-merge, auto-tag) is accepted out of scope; incremental normalization work is tracked in [ROADMAP.md](../ROADMAP.md) and [SPEC.md](SPEC.md) (normalization / metrics sections).

### 8.3 Normalization — full task list

| Task | Status | Notes |
|------|--------|--------|
| No duplicate IDs (claims, assumptions, symbols per paper) | **Done** | `validate_normalization` in pipeline; CI. |
| All edges resolve (linked_assumptions, linked_symbols) | **Done** | Same. |
| Symbol deduplication across papers | **Visibility + suggest merge** | Cross-paper duplicate normalized_name via `just metrics --normalization-report`; report includes `suggest_merge` (human triage); no auto-merge. |
| Variable role disambiguation | **Visibility** | Schema has `ambiguity_flags` (role_unclear); `just metrics --normalization-visibility` lists symbols with role_unclear; resolution remains manual. |
| Unit/dimension tagging | **Visibility + suggestions** | Schema supports dimensional_metadata; `just metrics --dimension-visibility` lists with vs without; `just metrics --dimension-suggestions` emits heuristic suggested unit/dimension from kernels and symbol names (human triage, no auto-edit). |
| Assumption lifting | **Visibility + suggestions** | `just metrics --normalization-visibility` lists claims with no linked_assumptions; `just metrics --assumption-suggestions` suggests candidates by text overlap (human triage). |
| Dependency edge inference | **Partial** | Theorem cards have `dependency_ids`; manifest derives `dependency_graph` from them. Lean source-based extraction populates same-file declaration dependencies. |

### Normalization maturity levels (acceptance progression)

| Level | Criteria | Enforcement |
|-------|----------|-------------|
| **v0.1** | No duplicate IDs per paper; all `linked_assumptions` and `linked_symbols` resolve. | `validate_normalization` in CI; fail-fast. |
| **v0.2** | Cross-paper symbol deduplication (normalized_name) applied or explicitly waived; unit/dimension tagging complete for symbols used in kernels. | Visibility and `normalization_report`; acceptance gate may require zero unwaived duplicates or documented waivers. |
| **v0.3** | Assumption lifting coverage: every claim has at least one linked assumption or an explicit waiver; kernel-linked symbols have dimensional_metadata. | Metrics and reports; optional CI threshold (e.g. coverage percentage). |

Progression: v0.1 is required for merge. v0.2/v0.3 are incremental; thresholds and waiver policies are set per milestone (see [ROADMAP.md](../ROADMAP.md) and [SPEC.md](SPEC.md)).

### Normalization waiver policy (policy-backed checks)

Optional policy file: `benchmarks/normalization_policy.json`. When present, `just metrics --normalization-policy` (or `just metrics` with default run-all) produces a machine-readable report:

- **duplicate_waivers:** list of `normalized_name` strings that are allowed to appear in multiple papers (waived); any other cross-paper duplicate is reported as `unwaived_duplicates`.
- **assumption_coverage_max_unlinked:** maximum allowed count of claims without linked assumptions; report sets `assumption_coverage_ok` to false and adds a warning when exceeded.
- **max_symbols_without_dimension:** maximum allowed count of symbols without `dimensional_metadata`; violations appended to `kernel_dimension_violations`.

Report keys: `policy_loaded`, `unwaived_duplicates`, `waived_duplicates`, `assumption_coverage_ok`, `assumption_coverage_message`, `kernel_dimension_violations`, `warnings`. Checks run in **warn-only** mode (warnings echoed to stderr); to enforce, add a CI step that fails when `unwaived_duplicates` is non-empty or `assumption_coverage_ok` is false, or when `warnings` is non-empty.

### Blueprint–mapping contract

Blueprint docs (e.g. `docs/blueprints/<paper>.md`) list claim IDs and target declarations; the canonical mapping lives in `corpus/papers/<paper_id>/mapping.json`. When they diverge, `mapping.json` is authoritative for the build. Use the optional `check-paper-blueprint` step (see [Adding a paper and a claim](#adding-a-paper-and-a-claim)) to report mismatches.

### Migration notes

- **2026-03**: Added optional `first_artifact_at` (date-time) to paper.schema.json; set by publish-artifacts when first writing manifest (median time intake→artifact can be computed from this). No migration required.

- **2026-03**: Added optional `ingestion_status` to paper.schema.json (enum: pending, ingested, failed) for SPEC 7.1. No migration required; existing corpus metadata need not populate it until tooling uses it.

- **2026-03**: Added `mapping.schema.json` for claim-to-declaration mapping (paper_id, namespace, claim_to_decl). No change to existing corpus; existing mapping.json files now validated in `validate-all`. Extended `validate_repo` to validate assumptions.json, symbols.json, and mapping.json per paper when present (SPEC Segment B).

- **2026-03**: Added optional `literature_error.schema.json` for per-paper `literature_errors.json` (array of { claim_id?, description, severity?, source }). Hand-maintained; used by research-value metrics when present. No migration required.

- **2026-03**: Added optional `target_file` to mapping.schema.json (path to Lean file containing declarations). Theorem card generator infers from namespace when absent (formal/Namespace/To/File.lean). Re-run `just publish-artifacts` (or publish-manifest per paper) to populate theorem_cards.json `file_path` from mapping.

- **2026-03**: Added `proof_repair_proposal.schema.json` for proof-repair proposal artifacts (human_review_only). Generated by `sm-pipeline proof-repair-proposals`; no corpus migration.

- **2026-03**: Added `mathematics` to paper.schema.json domain enum and pipeline Paper model for multi-domain slice (non-adsorption). No migration required for existing papers.

- **2026-03-18**: Added `proof_repair_apply_bundle.schema.json` for human-gated `proof-repair-apply` (find/replace patches under `formal/` only). No corpus migration; optional review JSON path in bundle.

- **2026-03-18**: Tightened theorem card reviewer contract: `reviewer_status` is now required in `theorem_card.schema.json` (enum unchanged), pipeline TheoremCard model updated to require reviewer_status, and `schemas/examples/theorem_card.example.json` updated to canonical Langmuir IDs plus reviewer_status. Validator rules now additionally enforce `accepted -> proof_status=machine_checked`. Existing generated theorem cards already include reviewer_status via publish.

## Release integrity (Gate 7)

SPEC Gate 7 requires: "Manifest signed; changelog generated; release artifact hash emitted." This section describes how the project satisfies Gate 7.

### How Gate 7 is satisfied

When a release is created (push to a tag `v*`), the [release workflow](../.github/workflows/release.yml) runs and [scripts/release_artifacts.sh](../scripts/release_artifacts.sh) produces:

1. **Changelog**  
   `dist/CHANGELOG.md` is generated from git log (from previous tag to HEAD, or last 20 commits if no prior tag). The workflow emits a short preview in the job log.

2. **Checksums**  
   `dist/checksums.txt` contains:
   - `manifest_checksum`: SHA-256 of the concatenated contents of all paper `manifest.json` files (sorted), so any change to manifests is detectable.
   - Per-file SHA-256 hashes of everything under `dist/`.
   - `release_artifact_sha256`: digest of the full release artifact content.

3. **Manifest signed**  
   The release workflow signs `dist/checksums.txt` with **Sigstore (cosign) keyless signing**. Signature and certificate are written to `dist/checksums.txt.sig` and `dist/checksums.txt.pem`. To verify a release: recompute checksums as above; if you have the `.sig` and `.pem` files, run `cosign verify-blob dist/checksums.txt --signature=dist/checksums.txt.sig --certificate=dist/checksums.txt.pem`. Checksum recomputation remains the primary tamper check; signing attests the origin (GitHub Actions OIDC).

### Publication (tagged releases)

When a version tag (`v*`) is pushed, the release workflow creates a **GitHub Release** and uploads publish-ready assets:

- `CHANGELOG.md` – changelog (previous tag to HEAD)
- `checksums.txt` – manifest and per-file checksums plus `release_artifact_sha256`
- `checksums.txt.sig` – Sigstore signature of `checksums.txt`
- `checksums.txt.pem` – Sigstore certificate
- `release-bundle.zip` – full `dist/` contents (corpus, changelog, checksums, signatures)

Verification instructions are deterministic: recompute checksums from the unpacked bundle and compare to `checksums.txt`; verify the signature with cosign as above.

### Verification

To verify a release locally:

- Clone at the release tag, run `just bootstrap` and `just build`.
- Optionally recompute hashes of `corpus/papers/*/manifest.json` and compare to the `manifest_checksum` published in the release’s `dist/checksums.txt`.

See [Running from a release](#running-from-a-release) for how to run from a release tag.

## Summary

| Goal                    | Command                                      |
|-------------------------|----------------------------------------------|
| Setup                   | `just bootstrap` then `just build`           |
| Validate corpus         | `just validate-corpus`                       |
| Benchmark smoke         | `just benchmark-smoke`                       |
| Add paper               | `just add-paper <paper_id>`                  |
| Extract claims (scaffold)| `just extract-claims <paper_id>`             |
| Scaffold formal         | `just scaffold-formal <paper_id>`            |
| Check one paper         | `just check-paper <paper_id>`                |
| Blueprint vs mapping    | `just check-paper-blueprint <paper_id>`     |
| Publish artifacts       | `just publish-artifacts <paper_id>`          |
| Scaffold gold           | `just scaffold-gold <paper_id>` (for each paper in `corpus/index.json`; update baseline `papers_with_gold` when adding papers) |
| Derived metrics         | `just metrics` (optional `-o report.json`; includes normalization-report with suggest_merge, dimension-suggestions) |
| Export diff baseline    | `just export-diff-baseline`                 |
| Check tooling (pandoc)  | `just check-tooling`                         |
| Extract from source     | `just extract-from-source <paper_id>` (pandoc + source/main.tex) |
| Build Verso             | `just build-verso` (see [Verso integration (optional)](#verso-integration-optional)) |
| MCP server              | `just mcp-server` (optional; tools: list_declarations_for_paper, list_declarations_in_file, get_dependency_graph_for_declaration; requires `uv sync --extra mcp`) |
| Full pre-PR check       | `just check`                                 |

Milestone 3 (20–40 machine-checked declarations) is **exceeded** at **62** machine-checked declarations across six papers (see [status/repo-snapshot.md](status/repo-snapshot.md), regenerated with `just repo-snapshot`). See [ROADMAP](../ROADMAP.md#content-target-milestone-3) for the content sprint checklist and stretch goals. Use the "Content sprint (Milestone 3)" issue template when opening a content-focused issue. The portal dashboard and `just metrics --proof-completion` reflect declaration totals.
