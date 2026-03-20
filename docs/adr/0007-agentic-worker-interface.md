# ADR 0007: Agentic worker interface (deferred implementation)

## Status

Accepted (documentation-first; implementation deferred).

## Context

Agents may propose corpus or formal edits. Verification must remain human-gated at merge time (Lean build, validate-all, portal build).

## Decision

- **Contract:** Tools expose read-only graph/manifest queries and proposal artifacts (`proof_repair_proposal`, `proof_repair_apply_bundle`). No autonomous write to `corpus/` or `formal/` without a human PR.
- **Apply path:** Only `sm-pipeline proof-repair-apply` with `--i-understand-human-reviewed` may modify `formal/` from a reviewed bundle. CI never runs apply.
- **Optional worker:** A future HTTP or queue worker would enqueue proposals for human review only; no auto-merge. MCP and CLI remain the reference integration surface until a product need justifies a worker service.

## Consequences

Documentation in [mcp-lean-tooling.md](../mcp-lean-tooling.md) describes the recommended agent loop. New worker code requires ADR amendment and security review.
