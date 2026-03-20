# ADR 0001: Monorepo

## Status

Accepted.

## Context

We need a single repo for corpus, formalization, pipelines, kernels, and portal so that versioning, CI, and cross-references stay consistent.

## Decision

Use a monorepo with clear directories: corpus, formal, schemas, pipeline, kernels, portal, benchmarks, scripts, docs. Build systems: Lake (Lean), uv (Python), pnpm/turbo (Node).

## Consequences

Single clone and tag for a release; CI must run all relevant builds and validations.
