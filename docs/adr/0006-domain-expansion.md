# ADR 0006: Domain expansion policy

## Status

Accepted.

## Context

SPEC 15 recommends a first domain (theoretical chemistry / adsorption) and allows expansion. We need an explicit policy for adding new domains so that corpus, portal, and docs stay consistent.

## Decision

- The first supported domain is chemistry/adsorption (SPEC 15). Papers use a `domain` field in metadata and `corpus/index.json`.
- **Update:** `domain` is a **closed enum** in `paper.schema.json` (chemistry, mathematics, physics, probability, control, quantum_information, other). Adding a new allowed domain requires extending the schema, the pipeline `Paper` model, a migration note in [Schema versioning and migration notes](../contributor-playbook.md#schema-versioning-and-migration-notes), and updating [Domain policy](../contributor-playbook.md#domain-policy) as needed.
- Adding a paper in an **existing** domain: set `domain` in metadata; run `just build-index`; follow intake and formalization workflow.
- Domain expansion is content and documentation work; no new pipeline or portal routes are required per domain.

## Consequences

- Domain policy is explicit; second domain (e.g. physics theory or probability, per SPEC 15) can be added by following the same pattern.
- Roadmap and contributor docs can reference this ADR for "how to add a paper from a new domain."
