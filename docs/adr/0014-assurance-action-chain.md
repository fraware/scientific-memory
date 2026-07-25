# ADR 0014: Assurance action-chain ontology and immutability

## Status

Accepted.

## Context

Scientific Memory is claim-centric: corpus JSON, Lean formalization, and PCS release import into `corpus/pcs/claims/`. Closest outcome surfaces (`ResultArtifact.v0`, `RuntimeReceipt.run_outcome`) do not model scientific outcomes, calibration against decisions, or an append-only chain from decision-time evidence through post-hoc calibration.

Autonomous science / assurance work needs durable, versioned records for outcomes and calibration, plus a portable action-chain graph that reuses PCS as the evidence layer without rewriting historical claims.

## Decision

### Ownership

- **Scientific Memory owns** domain semantics for outcomes, calibration, and action chains under `schemas/assurance/*.v1.schema.json` with instance `schema_version: "v1"`.
- **PCS remains** the portable evidence / claim protocol (`schemas/pcs/*.v0`). Assurance records reference PCS claim IDs and digests; they do not redefine PCS artifact types.
- External systems (VSA, AKTA, SCOPE, PF) are consumed as typed `ExternalArtifactRef` plus optional committed snapshots inside an assurance release. This layer has no live network clients.

### Node classes (scientific action chain)

Decision-time: `source`, `evidence`, `claim`, `proposed_action`, `admissibility_decision`, `review`, `grant`.

Runtime: `runtime_action`, `verification_result`.

Post-hoc: `outcome`, `replication`, `calibration_update`.

Edges are typed directed links between node IDs. The chain is a DAG; cycles are rejected.

### Immutability

- Storage: `corpus/assurance/actions/<action_id>/` with `nodes/`, `edges/`, `outcomes/`, `calibrations/`, import reports, and `graph_manifest.json`.
- Node and edge JSON are content-addressed. Updates append new nodes and edges only. Overwriting an existing node file with a different content digest is an error; identical digest is idempotent.
- Outcome, replication, and calibration appends never mutate PCS or corpus claim JSON, status, or digests.

### Fail closed

Missing refs, digest mismatch, unknown schema version, lifecycle conflict, or ambiguous dual IDs yield an explicit error or indeterminate status — never silent acceptance.

### Evidence class separation

Reuse PCS vocabulary: `formally_checked`, `certificate_checked`, `runtime_observed`, `empirically_measured`, `human_reviewed`, `unchecked_advisory`. UI and metrics must not promote lower classes to higher ones.

### Non-claims

- Scientific Memory is **not** the live authorization or execution system.
- One failed experiment is **not** definitive refutation of a claim.
- Presence of an outcome or calibration record is **not** claim acceptance.
- Outcomes and calibrations **never** automatically rewrite accepted claims.

## Consequences

- New schemas under `schemas/assurance/`; Pydantic models and CLI under `sm_pipeline.assurance` (`sm` / `sm-pipeline`).
- Corpus PCS artifacts remain `*.v0`; assurance artifacts use explicit `*.v1` filenames (see [ADR 0005](0005-schema-versioning.md) migration notes).
- Portal reads only the generated assurance export (`portal/.generated/assurance-export.json`), privacy-redacted for public builds by default.
- Metrics category `autonomous-science` reports visible denominators and exclusions.
- Operator docs: [docs/assurance/](../assurance/README.md).
