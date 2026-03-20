# ADR 0003: Claim bundle

## Status

Accepted.

## Context

The unit of traceability from source to formal artifact should be explicit and auditable.

## Decision

The core unit is the claim bundle: one claim ID, source span, linked assumptions, linked symbols, and optional formal targets (Lean declarations) and theorem cards. No public theorem card without a linked claim ID. No claim without a source span.

## Consequences

Extraction and formalization workflows produce and consume claim bundles; validation enforces linkage rules.
