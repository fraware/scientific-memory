# Documentation

Scientific Memory turns structured science into machine-checkable artifacts—corpus papers, Lean formalizations, executable kernels, and a portal that renders exclusively from canonical JSON—and this index serves as the entry point for contributors, integrators, and reviewers.

## Start here

| Document | Audience | What you get |
|----------|----------|--------------|
| [contributor-playbook.md](contributor-playbook.md) | Contributors | Setup, local checks, add a paper, review, releases |
| [CONTRIBUTING.md](../CONTRIBUTING.md) | Contributors | Rules and required validation |
| [architecture.md](architecture.md) | Contributors | Monorepo layout and validation flow |
| [SPEC.md](SPEC.md) | Maintainers / designers | Product and engineering specification |

## Proof-Carrying Science (PCS)

Optional integration with [pcs-core](https://github.com/SentinelOps-CI/pcs-core) imports signed releases, renders evidence in the portal, and publishes benchmark output for [pcs-bench](https://github.com/fraware/pcs-bench).

| Document | Purpose |
|----------|---------|
| [pcs/README.md](pcs/README.md) | Hub (quick start, release checklist, CI) |
| [pcs/import-and-releases.md](pcs/import-and-releases.md) | Import bundles and full releases |
| [pcs/benchmark-producer.md](pcs/benchmark-producer.md) | Produce `pcs_bench_ingest.v0.json` |
| [pcs/bench-ingest-contract.md](pcs/bench-ingest-contract.md) | Ingest schema and validation |
| [pcs/portal-rendering.md](pcs/portal-rendering.md) | Claim page layout contract |

Legacy paths (`PCS_PRODUCER.md`, `pcs-labtrust-import.md`, etc.) redirect into `docs/pcs/`.

## Reference

| Document | Purpose |
|----------|---------|
| [paper-intake.md](paper-intake.md) | Admitting papers and optional metadata |
| [metrics.md](metrics.md) | Derived metrics and benchmark tasks |
| [generated-artifacts.md](generated-artifacts.md) | Generated files and how they are produced |
| [pipeline-extension-points.md](pipeline-extension-points.md) | Extending pipeline stages |
| [reference/trust-boundary-and-extraction.md](reference/trust-boundary-and-extraction.md) | Canonical vs suggestion artifacts |
| [status/repo-snapshot.md](status/repo-snapshot.md) | Generated corpus snapshot (`just repo-snapshot`) |
| [ROADMAP.md](../ROADMAP.md) | Planned versions and content targets |

## Operations and infrastructure

| Document | Purpose |
|----------|---------|
| [maintainers.md](maintainers.md) | Public launch, branch protection, triage |
| [infra/README.md](infra/README.md) | CI workflows and required checks |
| [infra/release-policy.md](infra/release-policy.md) | Tagged releases and artifacts |
| [infra/cache-policy.md](infra/cache-policy.md) | CI cache keys |
| [operations/hard-wedge-stress-papers.md](operations/hard-wedge-stress-papers.md) | Hard-dimension intake scaffolds |

## Optional tooling

| Document | Purpose |
|----------|---------|
| [tooling/README.md](tooling/README.md) | Index of optional integrations |
| [tooling/mcp-lean-tooling.md](tooling/mcp-lean-tooling.md) | MCP server for Lean declarations |
| [tooling/pandoc-latex-integration.md](tooling/pandoc-latex-integration.md) | Pandoc / LaTeX source extraction |
| [tooling/prime-intellect-llm.md](tooling/prime-intellect-llm.md) | Suggest-only LLM proposals (human-gated apply) |

## Testing checklists

| Document | Purpose |
|----------|---------|
| [testing/trust-hardening-e2e-scenarios.md](testing/trust-hardening-e2e-scenarios.md) | Manual trust-boundary scenarios |
| [testing/llm-lean-live-test-matrix.md](testing/llm-lean-live-test-matrix.md) | LLM Lean assist operator matrix |
| [testing/llm-human-eval-rubric.md](testing/llm-human-eval-rubric.md) | Human review rubric for LLM sidecars |

## Narrative and decisions

| Location | Purpose |
|----------|---------|
| [blueprints/](blueprints/) | Per-paper claim maps (mapping in corpus remains canonical) |
| [playbooks/README.md](playbooks/README.md) | Role checklists (formalizer, reviewer, domain expander, release manager) |
| [adr/](adr/README.md) | Architecture decision records |

## Playbook quick links

[Public alpha](contributor-playbook.md#public-alpha-and-repository-state) · [Local CI](contributor-playbook.md#local-ci-checklist-green-before-merge) · [Reuse](contributor-playbook.md#reusing-scientific-memory) · [Theorem-card review](contributor-playbook.md#theorem-card-reviewer-lifecycle-policy) · [Verification boundary](contributor-playbook.md#verification-boundary) · [Schema migrations](contributor-playbook.md#schema-versioning-and-migration-notes) · [Release integrity](contributor-playbook.md#release-integrity-gate-7) · [PCS](pcs/README.md)
