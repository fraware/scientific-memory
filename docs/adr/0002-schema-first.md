# ADR 0002: Schema-first

## Status

Accepted.

## Context

Corpus and manifests must be machine-readable and validated. Ad-hoc formats would block tooling and portal generation.

## Decision

Define canonical JSON schemas for papers, claims, assumptions, symbols, theorem cards, kernels, and artifact manifests. Pipeline uses Pydantic models that mirror schemas. Validation runs on every CI and before publish.

## Consequences

Schema changes require coordinated updates to schemas, models, and fixtures; migration notes in docs.
