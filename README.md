<div align="center">

<img src="docs/assets/logo.png" alt="Scientific Memory logo" width="280">

# Scientific Memory

**Buildable, machine-checkable scientific knowledge.**

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Lean](https://img.shields.io/badge/Lean-4-teal.svg)](https://lean-lang.org/)
[![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![uv](https://img.shields.io/badge/uv-workspace-7056BF?logo=astral&logoColor=white)](https://docs.astral.sh/uv/)
[![pnpm](https://img.shields.io/badge/pnpm-monorepo-F69220?logo=pnpm&logoColor=white)](https://pnpm.io/)

[Quick start](#quick-start) · [Documentation](#documentation) · [Repository status](#repository-status) · [Contributing](#contributing)

</div>

---

## Overview

Scientific Memory turns mathematically structured science from prose into **machine-checkable, executable, composable artifacts** with full provenance. It is not a paper summarizer or a theorem leaderboard: it is a **knowledge-upgrading pipeline** built for durable scientific inheritance.

| You get | How |
|--------|-----|
| **Traceable claims** | Every claim anchored with `source_span` and schema-valid JSON |
| **Formal layer** | Lean 4 + mathlib, linked from the corpus via mapping and theorem cards |
| **Executable witnesses** | Kernels with explicit verification boundaries |
| **Inspectable output** | Portal rendered only from canonical manifests and exports |
| **Reproducible gates** | Unified validation, CI, benchmarks, and signed releases |

---

## Mission

The project optimizes for:

| Pillar | Meaning |
|--------|---------|
| Explicit claims & assumptions | No silent hand-waving between text and formal code |
| Formal declarations | Machine-checked where the project commits to it |
| Executable kernels | Where numerical or computational alignment matters |
| Versioned provenance | Artifacts you can audit and rebuild |
| Reproducible builds | Lean, Python, and portal all part of one bar |

---

## What lives here

| Area | Role |
|------|------|
| `corpus/` | Schema-first papers: metadata, claims, assumptions, symbols, manifests |
| `formal/` | Lean 4 library (`ScientificMemory`) linked to the corpus |
| `schemas/` | Canonical JSON Schema for all public artifacts |
| `pipeline/` | `sm_pipeline`: ingest, extract, validate (**gate engine**), publish, portal export |
| `kernels/` | Executable kernels + shared [`kernels/conformance/`](kernels/conformance/) test helpers |
| `portal/` | Next.js UI from `corpus-export.json` and corpus data |
| `benchmarks/` | Regression tasks, gold labels, thresholds, proof-success trends |

---

## Quick start

```bash
git clone https://github.com/fraware/scientific-memory.git
cd scientific-memory

just bootstrap    # toolchains and dependencies
just build        # Lean + portal + Python tests
just validate     # full corpus / schema / graph gates
just portal       # local dev server (see terminal for URL)
```

| Situation | Command |
|-----------|---------|
| Something failed early | `just doctor` (uv, pnpm, Lean, Lake) |
| Lean only | `just lake-build` or `just lake-build-verbose LOG=lake-build.log` |
| Full pre-PR sweep | `just check` |
| No `just` (e.g. Windows without Bash) | [Contributor playbook – Local CI](docs/contributor-playbook.md#local-ci-checklist-green-before-merge) |

---

## Repository status

<details>
<summary><strong>Current tree (corpus, pipeline, CI, metrics)</strong> — click to expand</summary>

- **Corpus:** Six admitted papers: Langmuir 1918, Freundlich 1906, and `temkin_1941_adsorption` (source-anchored chemistry/adsorption slices), `chem_dilution_reference` (dilution slice with two machine-checked claims, assumptions, and symbols) and `physics_kinematics_uniform` (15 machine-checked claims with full intake quality), and `math_sum_evens` (mathematics). Scaffold `test_new_paper` was retired from the index. Dependency graph is populated from Lean source extraction for theorem cards.
- **Pipeline:** Ingest (hash-source, build-index), extraction, normalization, mapping generation, **unified validation** ([`gate_engine`](pipeline/src/sm_pipeline/validate/gate_engine.py): schema, normalization, provenance, graph/kernel-theorem-card integrity, coverage, extraction_run for papers with claims, snapshot quality warnings), **optional stage orchestration** ([`pipeline_orchestrator`](pipeline/src/sm_pipeline/pipeline_orchestrator.py) for SPEC 8.x-shaped steps), publish (manifest, theorem cards, Lean-derived dependency_ids, kernel enrichment), and portal export via [`portal_read_model.build_portal_bundle`](pipeline/src/sm_pipeline/publish/portal_read_model.py) (`just export-portal-data`). **Automated tests:** **133** tests total (**107** under `pipeline/tests`, including benchmark regression, gold scorer, and source-span alignment checks; **26** under `kernels/adsorption/tests`). MCP contract/integration tests live in the pipeline suite. Run `just test` for the full check including smoke scripts. Refresh counts with `uv run pytest --collect-only -q`.
- **CI:** All seven gates in place (Lean build, schema + graph + migration checks, provenance, coverage, portal build + smoke test, benchmark regression with proof-success snapshot, per-paper slices, trend history, runtime budgets, minimum thresholds and **`tasks_ceiling`** upper bounds in `benchmarks/baseline_thresholds.json` (e.g. source-span alignment error rate on `tasks.gold`), release integrity). Gate 7: checksums plus **Sigstore (cosign) keyless signing**; tagged releases publish a **GitHub Release** with changelog, checksums, signatures, and `release-bundle.zip`. Verify script: `scripts/verify_release_checksums.sh`. **Quality:** Ruff on pipeline; tests as above.
- **Infra:** Policy docs in `infra/` (README, cache-policy, release-policy); CI and release under `.github/workflows/` and repo root.
- **Contributor tooling:** `just doctor` for environment diagnostics; stage banners in `just check`; `just lake-build` / `just lake-build-verbose LOG=...` for Lean build logs. SPEC and playbook use real paper ID `langmuir_1918_adsorption` in examples.
- **Metrics:** `just metrics` (median intake, dependency, symbol conflict, proof completion, axiom count, research-value including literature_errors, claims_with_clarified_assumptions, kernels_with_formally_linked_invariants, source-span alignment, normalization visibility, assumption-suggestions, dimension-visibility, dimension-suggestions). `just benchmark` writes `benchmarks/reports/latest.json` with `proof_success_snapshot`, `proof_success_summary.md`, and task outputs including **`tasks.gold`** (precision/recall/F1, `papers_with_gold`, and source-span alignment fields). Gate 6 compares against `benchmarks/baseline_thresholds.json` (`tasks` minima and `tasks_ceiling`). Use `just scaffold-gold <paper_id>` when admitting a paper (all indexed papers currently have gold).
- **Optional:** Blueprint check (`just check-paper-blueprint`), check-tooling (pandoc), extract-from-source, build-verso, mcp-server. Blueprints under `docs/blueprints/` cover Langmuir, Freundlich, `temkin_1941_adsorption`, and `physics_kinematics_uniform` (mapping mirror where present). **Role playbooks:** `docs/playbooks/` (formalizer, reviewer, domain-expander, release-manager). Portal dependencies pinned (Next.js ^14.2, React ^18.3) for reproducible builds. **Also:** Hypothesis-based property tests for adsorption kernels; shared kernel test helpers ([`kernels/conformance/`](kernels/conformance/) workspace package); theorem-card reviewer lifecycle ([contributor-playbook.md](docs/contributor-playbook.md#theorem-card-reviewer-lifecycle-policy)); `batch-admit --dry-run`; snapshot baseline quality validation; `validate-all --report-json` for gate reports; `just repo-snapshot` for [docs/status/repo-snapshot.md](docs/status/repo-snapshot.md).

</details>

---

## Artifact flow

```mermaid
flowchart LR
  subgraph inputs [Sources]
    Papers[Corpus JSON]
    Lean[Formal Lean]
  end
  subgraph pipeline [Pipeline]
    Gates[Gate engine]
    Pub[Publish and export]
  end
  subgraph outputs [Outputs]
    Portal[Portal]
    Bench[Benchmarks]
  end
  Papers --> Gates
  Lean --> Gates
  Gates --> Pub
  Pub --> Portal
  Gates --> Bench
```

---

## Documentation

| Topic | Link |
|-------|------|
| **Index** | [docs/README.md](docs/README.md) |
| **Contributor playbook** (setup, paper workflow, local CI, reuse, review, verification, Verso, schema migrations, Gate 7) | [docs/contributor-playbook.md](docs/contributor-playbook.md) |
| Architecture | [docs/architecture.md](docs/architecture.md) |
| Roadmap | [ROADMAP.md](ROADMAP.md) |
| Paper intake (SPEC 8.1) | [docs/paper-intake.md](docs/paper-intake.md) |
| Metrics (SPEC 12) | [docs/metrics.md](docs/metrics.md) |
| ADRs | [docs/adr/README.md](docs/adr/README.md) |
| Infra / CI policy | [infra/README.md](infra/README.md) |
| Repo snapshot | [docs/status/repo-snapshot.md](docs/status/repo-snapshot.md) (`just repo-snapshot`) |
| Maintainers (public push, CI, triage, launch) | [docs/maintainers.md](docs/maintainers.md) |
| MCP tooling (optional) | [docs/mcp-lean-tooling.md](docs/mcp-lean-tooling.md) |
| Pandoc / LaTeX (optional) | [docs/pandoc-latex-integration.md](docs/pandoc-latex-integration.md) |

---

## Contributing

| Resource | Link |
|----------|------|
| How to contribute | [CONTRIBUTING.md](CONTRIBUTING.md) |
| Step-by-step playbook | [docs/contributor-playbook.md](docs/contributor-playbook.md) |
| Pipeline extension points | [docs/pipeline-extension-points.md](docs/pipeline-extension-points.md) |

---

## Design principles

1. **Artifact-first, model-second** — durable JSON and Lean, not one-off prose.
2. **Provenance is mandatory** — claims and cards stay tied to sources.
3. **Verification boundaries are explicit** — proof vs witness vs heuristic is visible.
4. **Claim bundles are the core unit** — not isolated theorems in a void.
5. **Full buildability is the minimum bar** — no merge without the agreed gates.

---

## License

Licensed under **Apache-2.0** — see [LICENSE](LICENSE).
