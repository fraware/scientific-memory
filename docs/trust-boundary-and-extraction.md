# Trust boundary: canonical artifacts vs suggestions

This document fixes the **acceptance boundary** for Scientific Memory: what may enter merge gates and the portal read model, versus what is advisory only.

## Canonical layer (deterministic; gates enforce)

| Area | Role | Authoritative files |
|------|------|---------------------|
| Corpus | Claims, assumptions, symbols, mapping | `corpus/papers/<id>/*.json` (except sidecars below) |
| Formal | Machine-checked math | `formal/**/*.lean` |
| Publication | Manifest, theorem cards, portal export | `publish_manifest`, `theorem_cards.json`, `manifest.json`, `portal/.generated/corpus-export.json` |
| Validation | Schema, normalization, provenance, graph, coverage | `sm_pipeline.validate.gate_engine` |

LLM outputs **must not** bypass this layer. Models do not own validation, publication, coverage metrics, dependency graph truth in the manifest sense, or kernel linkage truth.

## Suggestion layer (human review; warn-only schema checks for some sidecars)

| Artifact | Purpose |
|----------|---------|
| `suggested_claims.json` | Pandoc / optional extractors; not canonical |
| `llm_claim_proposals.json`, `llm_mapping_proposals.json`, `llm_lean_proposals.json` | Prime Intellect proposal bundles (`human_review_only`; `metadata` uses [`llm_run_provenance.schema.json`](../schemas/llm_run_provenance.schema.json)); Lean bundle suggests find/replace pairs for human-gated `proof-repair-apply` only |
| `suggested_assumptions.json`, `suggested_symbols.json`, `suggested_mapping.json` | Structured suggestion wrappers (schemas under `schemas/`); promote only after review |

Promotion path: review → merge into canonical JSON → `just publish-artifacts` → `just validate`.

## Risk register (code touchpoints)

| Risk | Location | Mitigation |
|------|----------|------------|
| Scaffold placeholder mistaken for real extraction | [`pipeline/src/sm_pipeline/extract/claims.py`](../pipeline/src/sm_pipeline/extract/claims.py) | Explicit `--mode` on `extract-claims`; `extraction_run.json` records `extraction_mode` and `placeholder_claim_written` |
| Unresolved links dropped silently | [`pipeline/src/sm_pipeline/extract/normalize.py`](../pipeline/src/sm_pipeline/extract/normalize.py) | Preserve IDs on `linked_*_unresolved` fields; audit in `normalization_report.json` |
| Stale `dependency_graph` / `kernel_index` on republish | [`pipeline/src/sm_pipeline/publish/manifest.py`](../pipeline/src/sm_pipeline/publish/manifest.py) | Recompute from current cards and `corpus/kernels.json` each publish (opt-out: `SM_PUBLISH_REUSE_MANIFEST_GRAPHS=1`) |
| Weak integrity fingerprint | [`pipeline/src/sm_pipeline/publish/manifest.py`](../pipeline/src/sm_pipeline/publish/manifest.py) | `build_hash_version` **2**: content-addressed digest of canonical inputs |
| LLM-proposed Lean edits applied without review | [`pipeline/src/sm_pipeline/cli/llm_proposals.py`](../pipeline/src/sm_pipeline/cli/llm_proposals.py), [`proof-repair-apply`](contributor-playbook.md#proof-repair-apply-human-gated-formal-tree-only) | Generation writes only `llm_lean_proposals.json`; promotion uses `llm-lean-proposals-to-apply-bundle` then `proof-repair-apply` with explicit acknowledgement; `lake build` + `validate-all` remain the bar |
| Dependency edges are heuristic | [`pipeline/src/sm_pipeline/formalize/lean_deps.py`](../pipeline/src/sm_pipeline/formalize/lean_deps.py) | Theorem cards carry `dependency_extraction_method: lean_source_regex_tier0` |

## Model provenance

Every LLM run that produces committed suggestion artifacts should record provider, model, parameters, prompt template hash, input digests, token usage, and timestamps (see [`schemas/llm_run_provenance.schema.json`](../schemas/llm_run_provenance.schema.json) and [prime-intellect-llm.md](prime-intellect-llm.md)).

## Related ADRs

- [ADR 0007](adr/0007-agentic-worker-interface.md) — human-gated apply; no autonomous corpus writes
- [ADR 0008](adr/0008-llm-worker-deferred.md) — historical v0.1 deferral; optional worker added later
- [ADR 0011](adr/0011-llm-worker-suggest-only.md) — Prime Intellect suggest-only CLI
- [ADR 0012](adr/0012-trust-boundary-canonical-artifacts.md) — canonical publish and hash semantics

## Manual E2E checklist

Step-by-step scenarios (scaffold modes, normalization, sidecars, publish/hash) are in [testing/trust-hardening-e2e-scenarios.md](testing/trust-hardening-e2e-scenarios.md).
