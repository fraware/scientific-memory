# ADR 0008: LLM worker interface deferred

## Status

Accepted.

## Context

SPEC 10.1 lists optional ADR topics including "LLM worker interface." The spec emphasizes artifact-first principles and defers optional MCP/LSP tooling. For v0.1, extraction and normalization are human-curated or script-based; no LLM-assisted extraction pipeline is in scope.

## Decision

No LLM worker interface in v0.1. Extraction and normalization are performed by humans or deterministic scripts. When we introduce LLM-assisted extraction later, we will add a separate ADR for the worker interface (prompts, schema-bound outputs, replaceability, and integration with the existing validation gates).

## Consequences

- v0.1 scope remains focused on schema, corpus, formalization, and portal without an LLM dependency.
- Future LLM integration will be designed explicitly (worker interface, schema-bound outputs, audit trail) and documented in a follow-up ADR.
