# LLM proposal human evaluation rubric

Use this rubric when reviewing `llm_*_proposals.json` sidecars before any human-gated apply. It complements automated checks (JSON Schema, `tasks.llm_eval` reference fixtures, `tasks.gold` on canonical corpus after merge, and `lake build` after Lean apply).

## Dimensions

| Dimension | Question | Pass hint |
|-----------|----------|-----------|
| **Grounding** | Does each claim proposal’s `source_span` and `evidence_quote` match the real source text? | Spot-check against `corpus/papers/<id>/source/`. |
| **Completeness** | For the task (claims, mapping, Lean), are obvious items missing that a careful reader would expect? | Compare to gold or prior manual extraction when available. |
| **Mapping plausibility** | Does `lean_declaration_short_name` match an actual declaration in the mapped Lean file? | Grep or MCP declaration list. |
| **Lean safety** | For Lean proposals: is each `find` unique in `target_file`, under `formal/`, and minimally invasive? | Run static checks; dry-run `proof-repair-apply` before `--apply`. |
| **Minimality** | Are edits the smallest reasonable change, not a full-file rewrite? | Reject bloated replacements unless justified in `rationale`. |

## Workflow metadata

After review, record intent in bundle `metadata` when you promote or discard runs (see [`schemas/llm_run_provenance.schema.json`](../../schemas/llm_run_provenance.schema.json)): `reviewer_decision` (`pending` | `accepted` | `rejected` | `edited`), optional `promotion_outcome`, `notes`.

## Periodic audit (recommended)

- Sample **N** proposals per quarter (mix of claim, mapping, Lean).
- Prefer **two** independent reviewers on a subset; note agreement.
- File a short log entry in [llm-lean-live-test-matrix.md](llm-lean-live-test-matrix.md) or team tracker.

## Automation boundary

Automated metrics (`tasks.llm_suggestions`, `tasks.llm_lean_suggestions`, `tasks.llm_eval`, `llm_prompt_templates` in benchmark reports) are **regression and observability** signals. They do not replace this rubric for semantic correctness.
