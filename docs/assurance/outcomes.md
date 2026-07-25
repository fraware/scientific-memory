# ScientificOutcomeRecord.v1

Field semantics for durable scientific outcome records. Presence of a record does **not** constitute claim acceptance.

## Identity

| Field | Meaning |
|-------|---------|
| `outcome_id` | Stable outcome identity |
| `action_id` | Parent scientific action chain |
| `scientific_question_id` | Question under investigation |
| `claim_ids` | Related claim IDs (corpus or PCS); never rewritten by this record |
| `proposed_action_id` | Decision-time proposed action |

## External and PCS refs

`external_refs` holds typed `ExternalArtifactRef` entries (VSA, AKTA, SCOPE, PF, execution, other) with digests and lifecycle. `pcs_claim_ids` lists PCS claim IDs already in corpus when pointers are used.

## Result semantics

- `measured_result.result_kind` includes `not_yet_available` / `indeterminate` for explicit missingness.
- `delayed_result_status`: `not_delayed` | `delayed_unresolved` | `delayed_resolved`.
- `missing_data.has_missing_data` plus `fields[]` with reasons — never invent values.

## Integrity

`integrity` envelope: `content_digest`, `writer_identity`, `schema_version: "v1"`, `created_at`. Digest mismatch fails closed.

## Non-claim

Recording an outcome does not accept, reject, or rewrite PCS or corpus claims. Append with:

```bash
uv run --project pipeline sm add-outcome path/to/ScientificOutcomeRecord.v1.json
```
