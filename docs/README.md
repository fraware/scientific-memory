# Documentation index

| Start here | Purpose |
|------------|---------|
| [SPEC.md](SPEC.md) | Canonical product and engineering spec |
| [architecture.md](architecture.md) | Monorepo layout and validation flow |
| [contributor-playbook.md](contributor-playbook.md) | Onboarding, local CI (no `just`), reuse, review, verification, Verso, schema migrations, Gate 7 releases, add a paper / claim |
| [CONTRIBUTING.md](../CONTRIBUTING.md) | Contribution rules and local checks |
| [maintainers.md](maintainers.md) | Public push checklist, clean-room, branch protection, triage, launch cadence |

| Reference | Purpose |
|-----------|---------|
| [paper-intake.md](paper-intake.md) | SPEC 8.1 intake and optional `metadata.yaml` note |
| [metrics.md](metrics.md) | Metrics and gold benchmarks (SPEC 12) |
| [generated-artifacts.md](generated-artifacts.md) | What is generated and how |
| [infra/README.md](infra/README.md) | CI, release, and cache policy docs |
| [ROADMAP.md](../ROADMAP.md) | Versions and content targets |
| [adr/README.md](adr/README.md) | Architecture decision records |

| Optional tooling | Purpose |
|------------------|---------|
| [tooling/mcp-lean-tooling.md](tooling/mcp-lean-tooling.md) | MCP server |
| [tooling/pandoc-latex-integration.md](tooling/pandoc-latex-integration.md) | Pandoc / LaTeX extraction |
| [pipeline-extension-points.md](pipeline-extension-points.md) | Extending pipeline stages; blueprint / leanblueprint note |
| [tooling/prime-intellect-llm.md](tooling/prime-intellect-llm.md) | Optional Prime Intellect LLM proposals (suggest-only; human-gated apply) |
| [reference/trust-boundary-and-extraction.md](reference/trust-boundary-and-extraction.md) | Canonical vs suggestion artifacts; risk register touchpoints |

| Operations | Purpose |
|------------|---------|
| [operations/hard-wedge-stress-papers.md](operations/hard-wedge-stress-papers.md) | Intake-only hard-dimension scaffold policy |

| Per-paper narrative | |
|---------------------|---|
| [blueprints/](blueprints/) | Blueprint-style claim maps (mapping remains canonical) |
| [playbooks/](playbooks/) | Role-specific checklists |
| [status/](status/) | Generated status (e.g. repo snapshot) |
| [testing/trust-hardening-e2e-scenarios.md](testing/trust-hardening-e2e-scenarios.md) | Manual checklist for extraction modes, normalization, sidecars, publish/hash (complements automated tests) |
| [testing/llm-lean-live-test-matrix.md](testing/llm-lean-live-test-matrix.md) | Operator checklist for LLM Lean assist (fake vs live provider, model routing, apply path) |
| [testing/llm-human-eval-rubric.md](testing/llm-human-eval-rubric.md) | Human review rubric for LLM proposal sidecars (before apply) |

**Playbook sections (same file):** [public alpha](contributor-playbook.md#public-alpha-and-repository-state) · [local CI](contributor-playbook.md#local-ci-checklist-green-before-merge) · [reuse](contributor-playbook.md#reusing-scientific-memory) · [reviewer / theorem-card lifecycle](contributor-playbook.md#theorem-card-reviewer-lifecycle-policy) · [verification boundary](contributor-playbook.md#verification-boundary) · [Verso](contributor-playbook.md#verso-integration-optional) · [schema versioning](contributor-playbook.md#schema-versioning-and-migration-notes) · [release integrity](contributor-playbook.md#release-integrity-gate-7) · [domain policy](contributor-playbook.md#domain-policy)
