# Architecture Decision Records (ADR) index

SPEC 10.1 requires ADRs for major design decisions. This directory is the single index of all ADRs. Each record documents the context, decision, and consequences for a significant architectural choice.

| ADR | Title | Summary |
|-----|--------|---------|
| [0001](0001-monorepo.md) | Monorepo | Single repo for corpus, formalization, pipelines, kernels, and portal; Lake, uv, pnpm. |
| [0002](0002-schema-first.md) | Schema-first | Canonical JSON schemas for all corpus and manifest artifacts; validation on every CI. |
| [0003](0003-claim-bundle.md) | Claim bundle | Claim bundle as the unit of traceability; no theorem card without claim ID, no claim without source span. |
| [0004](0004-json-storage.md) | JSON storage for corpus and manifests | Use JSON (not YAML) for all corpus and manifest files. |
| [0005](0005-schema-versioning.md) | Schema versioning | Schema `$id` and version; migration notes in [contributor-playbook.md](contributor-playbook.md#schema-versioning-and-migration-notes); no auto-migration in v0.1. |
| [0006](0006-domain-expansion.md) | Domain expansion policy | First domain chemistry/adsorption; new domains via metadata and docs, no schema enum. |
| [0007](0007-pydantic-models.md) | Pydantic for pipeline models | Pipeline internal models mirror schemas via Pydantic; type validation and JSON round-trip. |
| [0008](0008-llm-worker-deferred.md) | LLM worker interface deferred | No LLM-assisted extraction in v0.1; human-curated or script-based only. |
| [0009](0009-unit-system-deferred.md) | Unit system deferred | Kernel `unit_constraints` (strings) only; formal dimension/unit system in Lean deferred. |
| [0010](0010-release-integrity-checksums.md) | Release integrity via checksums | Changelog, manifest checksum, per-file hashes, release artifact SHA-256; Sigstore keyless signing of checksums.txt. |
| [0011](0011-llm-worker-suggest-only.md) | LLM worker (suggest-only) | Optional Prime Intellect chat completions; claim/mapping/Lean proposal sidecars; human-gated apply (`proof-repair-apply` for Lean); warn-only schema check for sidecars. |
| [0012](0012-trust-boundary-canonical-artifacts.md) | Trust boundary and publish integrity | Recompute manifest graphs; content-addressed build hash; normalization preserves unresolved links; canonical vs suggestion artifacts. |
| [0013](0013-llm-evaluation-policy.md) | LLM evaluation policy | Prompt template digests; `benchmarks/llm_eval` reference fixtures; `tasks.llm_eval`; human rubric; optional live-eval scripts. |

When adding a new ADR, use the next number (e.g. 0014) and add a row to this table.
