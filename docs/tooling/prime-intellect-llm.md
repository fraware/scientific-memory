# Prime Intellect LLM integration (suggest-only)

This repository integrates [Prime Intellect](https://www.primeintellect.ai/)
inference (OpenAI-compatible chat completions) for **optional, human-reviewed**
assistance. LLM output is **never** a source of truth for the portal: canonical
data remains `corpus/` JSON and `formal/` Lean, validated by the gate engine.

**API reference:**
[Chat completions](https://docs.primeintellect.ai/api-reference/inference-chat-completions)
(base URL `https://api.pinference.ai/api/v1`).

## Configuration

1. Copy [`.env.example`](../../.env.example) to `.env` at the **repository
   root** (gitignored).
2. Set `PRIME_INTELLECT_API_KEY` (or `SM_PRIME_INTELLECT_API_KEY`).
3. Optional: `PRIME_INTELLECT_TEAM_ID` for team accounts;
   `PRIME_INTELLECT_BASE_URL` if the endpoint changes;
   `SM_LLM_MODEL_CLAIMS` / `SM_LLM_MODEL_MAPPING` / `SM_LLM_MODEL_LEAN` /
   `SM_LLM_MODEL_DEFAULT` for model routing.

Environment variables are loaded from root `.env` when you run CLI commands
(non-destructive: existing shell env wins).

## Commands

Run from repo root with `uv`:

```bash
uv run --project pipeline python -m sm_pipeline.cli llm-claim-proposals --paper-id <paper_id>
uv run --project pipeline python -m sm_pipeline.cli llm-mapping-proposals --paper-id <paper_id>
uv run --project pipeline python -m sm_pipeline.cli llm-lean-proposals --paper-id <paper_id>
```

Optional focus hint for Lean assist: `--decl <short_name_or_hint>`.

Outputs (by default):

- `corpus/papers/<paper_id>/llm_claim_proposals.json`
- `corpus/papers/<paper_id>/llm_mapping_proposals.json`
- `corpus/papers/<paper_id>/llm_lean_proposals.json`

Schemas:
[`schemas/llm_claim_proposals.schema.json`](../../schemas/llm_claim_proposals.schema.json),
[`schemas/llm_mapping_proposals.schema.json`](../../schemas/llm_mapping_proposals.schema.json),
[`schemas/llm_lean_proposals.schema.json`](../../schemas/llm_lean_proposals.schema.json).
Bundles carry `verification_boundary: "human_review_only"`.

### Lean suggestions (surgical; formal tree unchanged until you apply)

`llm-lean-proposals` writes **find/replace-oriented** suggestions only. It does
**not** modify `formal/`. After review, convert one entry to a
`proof_repair_apply` bundle and preview with `proof-repair-apply` (no
`--apply`), then apply with explicit human-review flags (see
[Contributor playbook – Proof-repair apply](../contributor-playbook.md#proof-repair-apply-human-gated-formal-tree-only)):

```bash
uv run --project pipeline python -m sm_pipeline.cli llm-lean-proposals-to-apply-bundle path/to/llm_lean_proposals.json --proposal-id <id> -o /tmp/lean_apply_bundle.json
uv run --project pipeline python -m sm_pipeline.cli proof-repair-apply /tmp/lean_apply_bundle.json
uv run --project pipeline python -m sm_pipeline.cli proof-repair-apply /tmp/lean_apply_bundle.json --apply --i-understand-human-reviewed
```

**Tests / no network:** pass `--use-fake-provider` to write a stub-backed
artifact (for CI and local plumbing checks).

**Model availability:** Some catalog models return HTTP 404 when no backend
route exists for your account. Tested models:
`allenai/olmo-3.1-32b-instruct` (all surfaces working). Default fallback
`meta-llama/llama-3.1-70b-instruct` may require account-specific routing
verification. See
[testing/llm-lean-live-test-matrix.md](../testing/llm-lean-live-test-matrix.md).

### Apply (human-gated)

After editing the proposal JSON to your satisfaction:

```bash
uv run --project pipeline python -m sm_pipeline.cli llm-apply-claim-proposals path/to/llm_claim_proposals.json
uv run --project pipeline python -m sm_pipeline.cli llm-apply-mapping-proposals path/to/llm_mapping_proposals.json
```

Dry-run prints a unified diff. To write:

```bash
uv run --project pipeline python -m sm_pipeline.cli llm-apply-claim-proposals path/to/llm_claim_proposals.json --apply --i-understand-human-reviewed
```

Claim apply **upserts by claim `id`** (preserves order of existing claims,
appends new ids). Mapping apply **merges** `claim_to_decl` keys from the
bundle.

Then run normalization/publish as usual (`just publish-artifacts <paper_id>`,
`just validate`, Lean build).

## Model provenance (`metadata`)

Proposal bundle `metadata` should conform to
[`schemas/llm_run_provenance.schema.json`](../../schemas/llm_run_provenance.schema.json)
(provider, model, `prompt_template_id`, `prompt_template_sha256`,
`input_artifact_sha256` with per-input SHA-256 digests, sampling parameters,
token usage, `reviewer_decision`, `promotion_outcome`, etc.). The pipeline sets
template id and digests from
[`pipeline/src/sm_pipeline/llm/prompt_templates.py`](../../pipeline/src/sm_pipeline/llm/prompt_templates.py)
on every generation run. Example:
[`schemas/examples/llm_run_provenance.example.json`](../../schemas/examples/llm_run_provenance.example.json).

**Human review:** use
[testing/llm-human-eval-rubric.md](../testing/llm-human-eval-rubric.md) before
apply.

**Smoke / live JSON report (optional):**
`just llm-live-eval --paper-ids <id> --use-fake-provider` or see
[`scripts/llm_live_eval.py`](../../scripts/llm_live_eval.py) (writes under
`benchmarks/reports/`, gitignored).

## Validation behavior

If `llm_*_proposals.json` (claims, mapping, Lean) or `suggested_*.json` files
are present under a paper directory, `validate-all` emits **non-blocking
warnings** when they fail JSON Schema validation. They are **not** part of the
canonical corpus schema gate.

## Governance

- ADR [0008](../adr/0008-llm-worker-deferred.md) deferred an LLM worker in
  v0.1; [0011](../adr/0011-llm-worker-suggest-only.md) records the suggest-only
  implementation boundary; [0013](../adr/0013-llm-evaluation-policy.md) records
  evaluation fixtures, benchmark task `llm_eval`, and the human rubric.
- Aligns with [0007](../adr/0007-agentic-worker-interface.md): no autonomous
  corpus/formal writes; explicit human confirmation for apply.

## Status and testing

**Live model testing:** Full end-to-end pipeline run completed on
`math_sum_evens` (branch `e2e-llm-pipeline-run`) with
`allenai/olmo-3.1-32b-instruct`. All three LLM surfaces (claims, mapping, Lean)
executed successfully; mapping proposal applied via human-gated workflow; all
verification gates passed. See
[testing/llm-lean-live-test-matrix.md](../testing/llm-lean-live-test-matrix.md)
for evidence log.

**Evaluation infrastructure:** Prompt template versioning, reference fixtures
under `benchmarks/llm_eval/`, benchmark task `llm_eval`, and human review rubric
are in place. See
[ADR 0013](../adr/0013-llm-evaluation-policy.md) and
[testing/llm-human-eval-rubric.md](../testing/llm-human-eval-rubric.md).
