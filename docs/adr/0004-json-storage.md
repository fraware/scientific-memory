# ADR 0004: JSON storage for corpus and manifests

## Status

Accepted.

## Context

SPEC 8.1 mentions `metadata.yaml` as paper intake output. The repo needs a single, consistent format for corpus files and manifests to simplify tooling, validation, and portal data loading.

## Decision

Use JSON (not YAML) for all corpus and manifest files: `metadata.json`, `claims.json`, `assumptions.json`, `symbols.json`, `mapping.json`, `manifest.json`, `theorem_cards.json`, and index files such as `corpus/index.json` and `corpus/kernels.json`. Pipeline, validators, and portal read/write JSON only.

## Consequences

- Consistent parsing and schema validation across the stack; no YAML dependency in the pipeline or portal.
- SPEC 8.1 wording ("metadata.yaml") is intentionally not followed literally; this ADR records the choice.
- YAML could be supported later (e.g. as an optional export or alternate intake path) if needed, without changing the canonical on-disk format.
