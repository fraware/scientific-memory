# ADR 0011: LLM worker (suggest-only) via Prime Intellect

## Status

Accepted.

## Context

ADR [0008](0008-llm-worker-deferred.md) deferred an LLM-assisted extraction pipeline for v0.1. Contributors still need optional model assistance for claim drafting and mapping suggestions while keeping merge gates deterministic and artifact-first (SPEC, ADR [0007](0007-agentic-worker-interface.md)).

## Decision

- Integrate **Prime Intellect** OpenAI-compatible **chat completions** (`https://api.pinference.ai/api/v1/chat/completions`) behind a small provider abstraction in the pipeline package.
- **Suggest-only default:** CLI writes `llm_claim_proposals.json`, `llm_mapping_proposals.json`, and `llm_lean_proposals.json` (surgical Lean find/replace suggestions) under each paper directory. These bundles use `verification_boundary: "human_review_only"` and JSON Schemas under `schemas/`.
- **Human-gated apply:** separate CLI commands merge reviewed claim/mapping bundles into `claims.json` / `mapping.json` only with `--apply --i-understand-human-reviewed`. Lean suggestions convert to `proof_repair_apply_bundle` and use `proof-repair-apply` (dry-run default; explicit flags to write `formal/`). Dry-run is the default for corpus merges.
- **CI / validate-all:** optional sidecars are validated with **warnings only** when present; they do not replace canonical schema validation for `claims.json` / `mapping.json`.
- **Secrets:** API key from environment or root `.env` (`PRIME_INTELLECT_API_KEY`); `.env` remains gitignored; `.env.example` documents variables.

## Consequences

- New dependencies: `httpx`, `python-dotenv` (pipeline package).
- Schema additions require the usual lockstep updates (models, examples, migration note).
- Future multi-provider routing can implement the same `LLMProvider` protocol without changing gate semantics.

## Relation to ADR 0008

ADR 0008 remains valid for historical scope (no LLM in v0.1 core path). This ADR records the **optional** suggest-only worker that does not bypass validation or portal read-model rules.
