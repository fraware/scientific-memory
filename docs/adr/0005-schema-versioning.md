# ADR 0005: Schema versioning

## Status

Accepted.

## Context

Schemas evolve; corpus and manifests must remain valid across changes. We need a clear policy for schema versions and migrations.

## Decision

- Schema identity and version are reflected in each schema's `$id` (e.g. `https://scientific-memory.org/schemas/paper.schema.json`). Breaking or additive changes are documented in [Schema versioning and migration notes](../contributor-playbook.md#schema-versioning-and-migration-notes) with migration notes.
- There is no automatic migration runner in v0.1. When a schema change is made, maintainers update corpus and fixtures manually (or via one-off scripts) and add a migration note to the contributor playbook.
- Pipeline validation uses the current schemas in `schemas/`; no multi-version validation.

## Consequences

- Single source of truth for "what changed and how to fix" in [contributor-playbook.md](../contributor-playbook.md#schema-versioning-and-migration-notes).
- New contributors and CI rely on the latest schemas only; no legacy version support in tooling for now.

## Migration notes (assurance)

- Assurance artifacts use explicit `*.v1` schema filenames under `schemas/assurance/` and instance field `schema_version: "v1"`.
- Corpus PCS artifacts remain `*.v0` under `schemas/pcs/`. Do not mix version families in a single artifact identity (a PCS claim stays `v0`; an assurance outcome stays `v1`).
- Assurance records may reference PCS claim IDs and digests; they must not rewrite PCS or corpus claim JSON.
- See [ADR 0014](0014-assurance-action-chain.md) and [docs/assurance/](../assurance/README.md).
