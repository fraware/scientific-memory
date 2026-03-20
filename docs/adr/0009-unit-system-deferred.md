# ADR 0009: Unit system deferred

## Status

Accepted.

## Context

SPEC 7.1 (Symbol) includes `dimensional_metadata`; SPEC 8.6 and workstream A mention a dimension/unit system. Executable kernels already have a `unit_constraints` field (array of strings). There is no formal dimension/unit system in the Lean formal layer yet.

## Decision

In v0.1 we use executable kernel **`unit_constraints`** (natural-language or short formal strings) as the only unit-related contract. Examples: "K and P non-negative", "coverage in [0, 1]". A formal dimension/unit system in Lean (and alignment of kernel constraints with it) is **deferred**. When we introduce it, we will add a follow-up ADR and align kernel schema, portal, and formal layer accordingly.

## Consequences

- Kernel pages and schemas remain the single place for unit expectations; no duplicate unit model in the formal layer until the deferred work.
- Symbol `dimensional_metadata` and workstream A dimension/unit system can be implemented later without breaking existing kernel or portal behavior.
