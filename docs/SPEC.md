# Scientific Memory — Project Specification

**Working name:** scientific-memory  
**Tagline:** Buildable, machine-checkable scientific knowledge.

This document is the canonical reference for the entire project. All engineering decisions, workstreams, and deliverables should align with this spec.

---

## 1. Overview and Architecture

Scientific Memory should be built as a **production-grade open-source monorepo** for proof-carrying scientific memory: a system that ingests mathematically structured scientific documents, converts their reusable core into machine-checkable Lean artifacts, links those artifacts to executable scientific kernels where possible, and publishes inspectable provenance-rich outputs.

**Stack:**

- **Formal:** Lean 4 with Lake as the build system, mathlib4 as the reusable formal substrate, blueprint-style project documentation for theorem/proof planning, optional Verso-backed long-form technical docs.
- **Context (as of February 2026):** Lean 4.28 is current; Lake supports remote artifact caching; mathlib4 remains the main community library; blueprint tooling is actively used across large Lean projects; Verso is used for Lean’s own long-form documentation.

**Scientific justification:** M2F shows project-scale end-to-end autoformalization in Lean across long-form mathematical sources; MerLean shows a full LaTeX-to-Lean-to-LaTeX review loop on quantum-computing papers; the 2HDM formalization found a non-trivial error in a widely cited physics paper; recent chemistry work in Lean shows how explicit assumptions and derivations can be encoded in a reusable scientific library. The scientific case justifies building infrastructure rather than demos.

---

## 2. Project Charter

### Mission

Transform mathematically structured scientific knowledge from prose into machine-checkable, executable, composable artifacts.

### What success looks like

A scientist can open a paper page in the project, inspect claims and assumptions, see which statements are formalized, inspect the dependency graph, run linked kernels, and trust that the artifact is reproducible and versioned.

### What this project is not

- Not a generic paper summarizer
- Not an LLM-first system (LLMs are optional, suggest-only workers; artifacts are canonical)
- Not “formalize all of science”
- Not a pure theorem library detached from source literature
- Not just a portal

**It is a knowledge-upgrading pipeline.**

---

## 3. Product Principles

Every engineering decision must satisfy these principles.

1. **Artifact-first, model-second.** LLMs are replaceable workers. The durable asset is the artifact graph.
2. **Source traceability is mandatory.** Every formal declaration must map back to a source claim, assumption, definition, or editorial note.
3. **Verification boundaries must be explicit.** The project must distinguish:
   - machine-checked proof
   - executable witness
   - numerical validation
   - heuristic extraction
   - human-reviewed prose mapping
4. **The public unit is the claim bundle, not the raw theorem.**
5. **Compilation is the minimum bar.** No artifact is “accepted” unless the full project builds end to end.
6. **Schema before UI.** The portal renders from canonical JSON/YAML artifacts, never from bespoke hand-written pages.
7. **One wedge first.** First domain: mathematically dense physical science / theoretical chemistry / dimensional analysis / probability foundations.

---

## 4. User Personas

The repo must support four users.

| Persona | Need |
|--------|------|
| **A. Formal methods contributor** | Write Lean code, definitions, proofs, tactics, libraries. |
| **B. Domain scientist** | Inspect what part of a paper is formalized, what assumptions were made, whether the result is computationally meaningful. |
| **C. Infrastructure engineer** | Stable schemas, CI, reproducibility, release process, caching, clean interfaces. |
| **D. Research evaluator / future model-training user** | Benchmarkable corpora with provenance and explicit acceptance labels. |

---

## 5. Top-Level Deliverables

### Version 0.1 (must ship)

1. A public monorepo that builds cleanly.
2. A canonical schema for: paper, claim, assumption, symbol, theorem card, executable kernel, artifact manifest.
3. At least one complete domain slice with: source paper, extracted claims, Lean formalization, dependency graph, artifact page.
4. A benchmark suite for the ingestion/formalization loop.
5. CI/CD that enforces provenance, buildability, and coverage thresholds.

### Version 0.2

- Multiple papers in one domain
- Claim coverage dashboards
- Assumption drift diffing
- Numeric witness testing
- Reviewer workflows
- **Optional LLM assistance** (suggest-only, human-gated apply; Prime Intellect integration for claims, mapping, and Lean proposals; evaluation infrastructure with prompt versioning, reference fixtures, benchmark task `llm_eval`)

### Version 0.3

- Proof repair (human-gated `proof-repair-apply` on `formal/`)
- Multi-domain expansion
- Public artifact releases
- External contributor playbooks
- Deeper automation (optional, beyond suggest-only)

---

## 6. Tech Stack

### Core formal layer

- Lean 4 pinned by `lean-toolchain`
- Lake for package and build management
- mathlib4 as primary dependency
- Blueprint tooling for theorem plan / dependency narrative
- Optional Verso for richer documentation if needed later

### Pipeline layer

- Python for ingestion / parsing / orchestration
- Pydantic models for internal typed objects (including optional **stage contracts** for SPEC 8.x-shaped runs)
- JSON Schema as external contract
- **Unified validation** via a gate runner (`sm_pipeline.validate.gate_engine`) and `validate-all --report-json` for machine-readable reports
- **Portal export** built from a single read-model projection (`sm_pipeline.publish.portal_read_model`)
- Optional **pipeline orchestrator** (`sm_pipeline.pipeline_orchestrator`) to compose intake → publish steps with structured `PipelineRunReport`
- pandoc, LaTeX parsers, XML/HTML utilities as needed
- Optional MCP/LSP-based Lean tooling later; not in v0.1

### Portal layer

- Next.js
- TypeScript
- pnpm monorepo
- Graph visualization library for dependency graph
- Static export for artifact pages
- Serverless API only if strictly necessary

### Infra layer

- GitHub Actions
- Artifact caching
- Containerized dev environment
- Deterministic test fixtures
- Pre-commit hooks

---

## 7. Canonical Data Model

This is the most important part of the spec.

### 7.1 Core entities

**Paper**

- id, title, authors, year
- DOI / arXiv / source links
- domain
- source files
- ingestion status, artifact status

**Claim**

- id, paper_id, section, source_span
- informal_text, claim_type, mathematical_density, status
- linked_symbols, linked_assumptions, linked_formal_targets

**Assumption**

- id, paper_id, source_span
- text, kind, explicit_or_implicit, normalization_status

**Symbol**

- id, paper_id, raw_latex, normalized_name, type_hint
- dimensional_metadata, ambiguity_flags

**TheoremCard**

- id, claim_id, lean_decl, file_path
- proof_status, dependency_ids, verification_boundary
- reviewer_status, executable_links, notes

**ExecutableKernel**

- id, domain
- input_schema, output_schema, semantic_contract, unit_constraints
- linked_theorem_cards, test_status

**ArtifactManifest**

- paper_id, version
- coverage_metrics, build_hash
- generated_pages, declaration_index, dependency_graph, kernel_index

### 7.2 Claim types (closed enum)

definition, theorem, lemma, proposition, corollary, estimator, identity, conservation_law, control_rule, dimensional_constraint, algorithmic_step, acceptance_criterion, editorial_exposition

### 7.3 Proof status enum

unparsed, parsed, mapped, stubbed, compiles_with_sorries, machine_checked, linked_to_kernel, disputed, superseded

### 7.4 Verification boundary enum

fully_machine_checked, machine_checked_plus_axioms, numerically_witnessed, schema_valid_only, human_review_only

---

## 8. End-to-End Workflow

### 8.1 Paper intake

- **Input:** PDF / arXiv source / LaTeX source, metadata file, chosen domain.
- **Output:** `corpus/papers/<paper-id>/metadata.yaml`, normalized source assets, initial parsing report.
- **Acceptance:** Paper metadata validated; source hash stored; reproducible ingestion command exists.

### 8.2 Claim extraction

- **Input:** Source assets, extraction prompt/pipeline, human review interface.
- **Output:** claims.yaml, assumptions.yaml, symbols.yaml.
- **Acceptance:** Every claim has source span; every assumption has provenance; ambiguity flags generated; extraction metrics recorded.

### 8.3 Normalization

- **Tasks:** Symbol deduplication, variable role disambiguation, unit and dimension tagging, assumption lifting, dependency edge inference.
- **Output:** Canonical symbol table, initial claim graph.
- **Acceptance:** No duplicate IDs; all edges resolve; unresolved ambiguities surfaced, not hidden.

### 8.4 Formal mapping

- **Tasks:** Map claim to existing foundations; identify new definitions; assign target Lean files; generate theorem stubs.
- **Output:** Target map, stub Lean declarations, blueprint linkage.
- **Acceptance:** Every mapped claim points to a file and declaration name; source claim ↔ formal declaration link stored bidirectionally.

### 8.5 Formalization

- **Tasks:** Implement definitions; discharge proofs; minimize axioms; record dependencies.
- **Output:** Compiling Lean files, theorem cards.
- **Acceptance:** Builds in CI; no hidden disconnected declarations; theorem cards generated automatically.

### 8.6 Executable kernel linkage

- **Tasks:** Identify computationally meaningful claims; create typed executable kernel; align units and invariants; run witness tests.
- **Output:** Linked kernel package, semantic contract, reproducible examples.
- **Acceptance:** Input/output schemas valid; unit checks pass; kernel page visible in portal.

### 8.7 Publication

- **Tasks:** Generate artifact manifest; update portal; emit coverage and dependency graph; attach release assets.
- **Acceptance:** Paper page renders; theorem cards render; declaration links work; release notes summarize delta.

---

## 9. Repo Workstreams

| Workstream | Ownership | Primary output |
|------------|-----------|-----------------|
| **A — Lean foundations** | Foundational types, assumptions framework, provenance structures, dimension/unit system, domain root namespaces, theorem-card extraction hooks | `formal/ScientificMemory/Foundations/*` |
| **B — Corpus and schema** | JSON Schemas, Pydantic models, validators, migration scripts, corpus fixtures | `schemas/*`, `pipeline/models/*`, `corpus/*` |
| **C — Ingestion and extraction** | Source ingest, parsing, claim extraction, normalization, source-span alignment, batch runners | `pipeline/ingest/*`, `pipeline/extract/*` |
| **D — Portal** | Public artifact pages, graph UI, claim/proof/kernels views, search, diff rendering | `portal/*` |
| **E — Benchmarks** | Benchmark task definitions, gold labels, scorer, dashboard exports, regression reports | `benchmarks/*` |
| **F — Infra and release** | GitHub Actions, devcontainers, Dockerfiles, release process, artifact caching, contributor DX | `infra/*`, `.github/workflows/*` |

---

## 10. Development Rules

### 10.1 ADRs

Every major design decision gets an Architecture Decision Record, including: schema versioning model; one repo vs multi-repo; Pydantic vs pure dataclasses; JSON vs YAML storage policy; unit system design; domain expansion policy; LLM worker interface.

### 10.2 Branching

- main always releasable
- Short-lived feature branches
- Squash merges
- Required checks before merge

### 10.3 Code review

Every PR must state: what artifact changes; what schemas changed; what coverage changed; what verification boundary changed; what new risk was introduced.

### 10.4 No magic output

If any generated file lands in git, its generator command must be documented.

### 10.5 Deterministic fixtures

All test fixtures must be pinned and hashed.

---

## 11. CI/CD Gates

These are mandatory.

| Gate | Scope |
|------|--------|
| **1 — Lean build** | Full Lake build, full test suite, no broken imports, cache usage enabled |
| **2 — Schema validation** | Every corpus object validates; migration checks pass; no orphan links |
| **3 — Provenance integrity** | Every claim has source span; every theorem card has originating claim; no dangling declaration refs |
| **4 — Coverage integrity** | Generated coverage report matches corpus state; no manual coverage edits allowed |
| **5 — Portal build** | Static build passes; all artifact routes generated; graph render smoke tests pass |
| **6 — Benchmark regression** | Task suite runs; extraction metrics do not regress above threshold; proof success metrics tracked; runtime budgets enforced |
| **7 — Release integrity** | Manifest signed; changelog generated; release artifact hash emitted |

---

## 12. Metrics

### Product metrics

- Number of papers admitted
- Number of claim bundles
- Percentage of claims with source spans
- Percentage of claims mapped to formal targets
- Percentage of mapped claims machine-checked
- Percentage linked to executable kernels
- Median time from paper intake to first artifact page

### Formalization metrics

- Declaration compile rate, proof completion rate
- Axiom count per paper
- Dependency reuse ratio
- Average theorem-card fan-in / fan-out
- Number of claims marked disputed after formalization

### Extraction metrics

- Claim extraction precision, assumption extraction recall
- Symbol normalization conflict rate, source-span alignment error rate

### Infra metrics

- Cold build time, cached build time, portal build time
- Flaky test rate, schema migration break rate

### Research-value metrics

- Reusable foundation count, cross-paper reuse count
- Literature error discoveries
- Number of claims whose assumptions were clarified materially
- Number of kernels with formally linked invariants

---

## 13. Milestones

| Milestone | Duration | Focus | Exit criteria |
|-----------|----------|--------|----------------|
| **0 — Repo bootstrap** | 1 week | Monorepo scaffold; Lean/Python/TS works; CI skeleton; contributor setup | New contributor can clone and build in under 30 minutes |
| **1 — Schema and corpus foundation** | 2 weeks | All core schemas; Pydantic models; first paper metadata template; validation CLI; sample corpus | One sample paper fully represented in canonical objects |
| **2 — First domain slice** | 3 weeks | First chosen paper; claims/assumptions/symbols; blueprint scaffold; first theorem stubs; artifact page prototype | One paper page renders from canonical data |
| **3 — Machine-checked core** | 4 weeks | 20–40 meaningful claims machine-checked; dependency graph; theorem cards auto-generated; source links visible | First credible end-to-end formal artifact |
| **4 — Executable linkage** | 2 weeks | One kernel family linked to formal content; witness tests; unit constraints; example notebooks/demos | User can inspect a theorem and run linked computational artifact |
| **5 — Benchmarking and public alpha** | 3 weeks | Benchmark suite; coverage dashboard; release workflow; docs and contributor guides; public alpha | Outside contributor can add a claim and pass CI |

**Repository snapshot (v0.2):** For current paper counts, machine-checked declaration totals per paper, `build_hash_version`, and dependency-graph edge counts, run `just repo-snapshot` and read [status/repo-snapshot.md](status/repo-snapshot.md) (generated; do not rely on this sentence for exact numbers). In aggregate, `corpus/index.json` lists six papers across adsorption, chemistry, mathematics, and physics slices; adsorption kernels use Hypothesis-based property tests plus pytest witnesses; proof-repair proposals plus human-gated `proof-repair-apply` (formal tree only) support maintainer workflows. Milestones 3–5 are largely satisfied in aggregate; further work is corpus depth in additional domains.

---

## 14. 90-Day Execution Plan

| Sprint | Focus |
|--------|--------|
| **1** | Bootstrap monorepo; choose first domain and paper; freeze schemas v0; establish CI and devcontainer |
| **2** | Corpus validation; claim extraction pipeline; symbol table and assumption normalizer; stub portal |
| **3** | Blueprint integration; Lean foundations; theorem card generator; first mapped claims |
| **4** | Prove first 10–15 claims; build graph explorer; build manifest generator; add regression tests |
| **5** | Executable kernel linkage; witness tests; paper page polishing; contributor templates |
| **6** | Benchmark suite; public alpha docs; release; roadmap for domain 2 |

---

## 15. First-Domain Recommendation

**Recommendation:** Theoretical chemistry / adsorption theory / dimensional and thermodynamic foundations, with an expansion path into physical theory and probability.

**Rationale:**

- Concrete Lean-based chemistry precedent exists
- Assumptions are explicit and pedagogically tractable
- Executable kernels are natural
- Rich enough to matter, bounded enough to ship
- Bridge to broader physical science formalization

**Second-best wedge:** Physics theory papers with strong mathematical structure; PhysLean/physlib and 2HDM/Lean-QuantumInfo ecosystem is organizing.

---

## 16. Portal Spec

The portal has five page types.

| Page | Content |
|------|---------|
| **A. Paper page** | Title, metadata, version; claim coverage; assumption list; declaration count; kernel count; disputed claims; graph entrypoint |
| **B. Claim page** | Source text, source span; normalized symbols; linked assumptions; formal status; linked Lean declaration; reviewer notes |
| **C. Theorem card page** | Declaration name, file path; proof status; dependency graph; linked claim; boundary type; linked kernels |
| **D. Kernel page** | Semantic role; input/output contract; linked theorems; unit constraints; reproducible runs; example outputs |
| **E. Diff page** | Version-to-version changes; assumption drift; new/broken proofs; status transitions |

---

## 17. Contributor Experience

Target flow for a first-time contributor:

```bash
git clone ...
just bootstrap
just build
just portal
just validate-corpus
just benchmark-smoke
```

Then (use a stable paper ID, e.g. `author_year_topic`; the example below uses the first domain slice ID):

```bash
just add-paper langmuir_1918_adsorption
just extract-claims langmuir_1918_adsorption
just scaffold-formal langmuir_1918_adsorption
```

Edit: claims, assumptions, Lean stubs, mapping file. Then:

```bash
just check-paper langmuir_1918_adsorption
```

If the project is hard to set up, open-source leverage is lost.

---

## 18. Acceptance Criteria for v0.1

All of the following must be true:

- We can admit a paper into the corpus reproducibly.
- We can extract and validate claims, assumptions, and symbols.
- We can map claims to Lean declarations.
- We can machine-check a meaningful subset.
- We can generate theorem cards automatically.
- We can render a public artifact page from canonical data.
- We can benchmark the extraction/formalization loop.
- We can onboard an external contributor without private tribal knowledge.

---

## 19. Risks and Mitigations

| Risk | Mitigation |
|------|-------------|
| Repo becomes an LLM demo | All workflows center on schemas and CI, not prompts |
| Formalization throughput too slow | Optimize around claim bundles, stubs, dependency planning, one wedge |
| Portal disconnected from formal truth | Portal renders only generated manifests |
| Overbuilding generic infrastructure before first artifact | Milestone 3 requires a single end-to-end paper before platform expansion |
| Theorem library drifts from source literature | Source span + claim ID mandatory for every public declaration |

---

## 20. Instruction for Engineers

Build this as a **schema-first, artifact-first, Lean-centered monorepo** for scientific knowledge upgrading.

- Do not optimize for demo polish before we have one full end-to-end paper artifact.
- The first 6 weeks should produce a paper page backed by canonical claim objects, Lean declarations, theorem cards, and a passing build.
- Every subsystem must answer one question: **does this help convert scientific prose into reusable, machine-checkable inheritance?**

---

*Document version: 1.0. Keep this file as the single source of truth for the project spec.*
