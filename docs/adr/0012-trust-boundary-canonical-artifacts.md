# ADR 0012: Trust boundary for canonical artifacts and publish integrity

## Status

Accepted.

## Context

Extraction and normalization are still largely bootstrap tooling. LLM integration increases throughput of suggestions but must not weaken what the portal and gates treat as true. Publication previously reused `dependency_graph` and `kernel_index` from an existing manifest when present, which could preserve stale graphs. `build_hash` hashed identifiers and paths, not full canonical payloads.

## Decision

1. **Canonical boundary** remains `claims.json`, `assumptions.json`, `symbols.json`, `mapping.json`, generated `theorem_cards.json` / `manifest.json`, and Lean sources. Suggestion files are non-canonical until promoted by humans.
2. **Publish** recomputes `dependency_graph` and `kernel_index` from current theorem cards and `corpus/kernels.json` on every `publish_manifest`, unless `SM_PUBLISH_REUSE_MANIFEST_GRAPHS=1` is set (escape hatch only).
3. **Theorem cards** record `dependency_extraction_method` for the current Tier-0 Lean source regex heuristic (`lean_source_regex_tier0`).
4. **build_hash_version 2** content-addresses claims, assumptions, symbols, mapping, theorem cards, metadata source hash, and kernel index for the paper manifest.
5. **Normalization** preserves unresolved claim link targets on optional `linked_assumptions_unresolved` / `linked_symbols_unresolved` instead of discarding them silently.

## Consequences

- Schema and pipeline model updates for claims, theorem cards, and manifests; migration note in contributor playbook.
- Re-running `publish-artifacts` updates manifests and may change `build_hash` for all papers.
- Human-readable trust contract: [trust-boundary-and-extraction.md](../reference/trust-boundary-and-extraction.md).
