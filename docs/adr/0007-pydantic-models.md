# ADR 0007: Pydantic for pipeline models

## Status

Accepted.

## Context

The pipeline ingests and emits data that mirrors the project's JSON schemas (claim, assumption, symbol, paper, manifest, executable kernel, etc.). We need a consistent approach for internal Python models: type validation, JSON round-trip, and alignment with the schema-first contract.

## Decision

Use Pydantic (not pure dataclasses) for pipeline internal models that mirror JSON schemas. Models live in `pipeline/.../models/` (or equivalent) and are kept in sync with the schema definitions. Validation and serialization use Pydantic's built-in support; schema evolution follows [Schema versioning and migration notes](../contributor-playbook.md#schema-versioning-and-migration-notes).

## Consequences

- Dependency on Pydantic; models benefit from runtime validation and JSON (de)serialization.
- Models must be updated when schemas change; migration and versioning are documented in the contributor playbook (schema versioning section) and ADR 0005.
- Consistency with a schema-first, artifact-first approach: the JSON schema remains the external contract; Pydantic models are the internal typed representation.
