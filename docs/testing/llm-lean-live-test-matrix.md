# LLM Lean assist: live and automated test matrix

This checklist supports [prime-intellect-llm.md](../tooling/prime-intellect-llm.md) and the `llm_lean_proposals` sidecar. **Canonical `formal/` is never modified by generation**; only `proof-repair-apply` with explicit human-review flags may write Lean after you review a converted bundle.

## Regression workflow (prompts and reference fixtures)

1. Prompts are versioned in [`pipeline/src/sm_pipeline/llm/prompt_templates.py`](../../pipeline/src/sm_pipeline/llm/prompt_templates.py); changing them updates `metadata.prompt_template_sha256` on new runs and the `llm_prompt_templates` map in `just benchmark` output.
2. Reviewed anchors live under [`benchmarks/llm_eval/`](../../benchmarks/llm_eval/README.md) (`reference_llm_*_proposals.json` per paper). After intentional prompt or behavior changes, regenerate or edit those files and run `just benchmark` (Gate 6 includes `tasks.llm_eval` minima).
3. Extended coverage: `uv run --project pipeline pytest pipeline/tests/test_llm_eval_harness.py -q`.
4. Optional smoke report: `just llm-live-eval --paper-ids math_sum_evens --use-fake-provider`.
5. Optional full Lean sanity after manual apply experiments: `LLM_EVAL_RUN_LAKE_BUILD=1 just llm-eval-lean-build-optional`.

## Automated (CI / local, no API key)

| Check | Command | Expected |
|-------|---------|----------|
| Unit + integration | `uv run --project pipeline pytest pipeline/tests/test_llm_lean_proposals.py pipeline/tests/test_benchmark_runner.py -q` | Pass |
| Full pipeline tests | `uv run --project pipeline pytest pipeline/tests -q` | Pass |
| LLM eval harness | `uv run --project pipeline pytest pipeline/tests/test_llm_eval_harness.py -q` | Pass; `tasks.llm_eval`, `llm_prompt_templates` |
| Sidecar schema | Covered by `test_validate_llm_lean_sidecar_invalid_warns` | Warn-only path for invalid `llm_lean_proposals.json` |
| Benchmark task | `tasks.llm_lean_suggestions` in `benchmark_runner.TASK_NAMES` | `just benchmark` includes keys: `llm_lean_proposal_files`, `lean_proposals_total`, `lean_proposals_conversion_ready`, `by_edit_kind` |
| Fake provider plumbing | `uv run --project pipeline python -m sm_pipeline.cli llm-lean-proposals --paper-id math_sum_evens --use-fake-provider -o tmp/live_matrix_fake_lean.json` | Writes valid bundle; `paper_id` forced to CLI value; `proposals` may be empty |

## Live tests (require `PRIME_INTELLECT_API_KEY` and a working model)

Prime Intellect may return **404** for some catalog models (no provider route for your account). Before relying on a model, confirm a minimal authenticated chat completion succeeds (see Live test A).

### Live test A: Provider and model sanity

1. Load `.env` from repo root (or export env vars).
2. `GET {PRIME_INTELLECT_BASE_URL or https://api.pinference.ai/api/v1}/models` with `Authorization: Bearer …` and pick a model id that returns **200** on a minimal `POST …/chat/completions` body (`messages: [{role:user,content:OK}]`).
3. Set `SM_LLM_MODEL_LEAN` to that model (optional `SM_LLM_MODEL_DEFAULT` fallback).

### Live test B: Small paper

```bash
uv run --project pipeline python -m sm_pipeline.cli llm-lean-proposals --paper-id math_sum_evens -o tmp/lean_math_sum_evens.json
```

Record: wall-clock time, `metadata.latency_seconds`, token fields, whether each proposal’s `find` is **unique** in the target Lean file (required for `proof-repair-apply`).

### Live test C: Larger paper

Repeat with `--paper-id langmuir_1918_adsorption` (or another multi-declaration paper). Compare proposal count and failure rate (empty `replacements` vs conversion-ready entries).

### Live test D: Converter and dry-run apply

1. Pick a proposal with non-empty `replacements` and `target_file` under `formal/`.
2. `uv run --project pipeline python -m sm_pipeline.cli llm-lean-proposals-to-apply-bundle tmp/lean_math_sum_evens.json --proposal-id <id> -o tmp/lean_apply_bundle.json`
3. `uv run --project pipeline python -m sm_pipeline.cli proof-repair-apply tmp/lean_apply_bundle.json` (no `--apply`) and inspect output.
4. Only if correct: `--apply --i-understand-human-reviewed` on a throwaway branch/worktree.

### Live test E: Pipeline after apply

After any real apply: `lake build` (or `just lake-build`), `just publish-artifacts <paper_id>`, `just validate`, `just benchmark`.

### Live test F: Guardrails

| Case | Expected |
|------|----------|
| Invalid `llm_lean_proposals.json` committed | `validate-all` stderr warning; exit **0** |
| Converter on proposal with empty `replacements` | `ValueError` with clear message |
| `target_file` outside `formal/` or contains `..` | Pydantic validation error on bundle load / converter refusal |

## Evidence log (fill on runs)

| Date (UTC) | Operator | Test | Model (`SM_LLM_MODEL_LEAN`) | Result / notes |
|------------|----------|------|----------------------------|----------------|
| 2026-03-20 | automation | Fake CLI `math_sum_evens` | `fake` | Valid JSON; `proposals: []` from default stub |
| 2026-03-20 | agent | Live eval `math_sum_evens` (real API) | `meta-llama/llama-3.1-70b-instruct` | Report: `benchmarks/reports/llm_live_20260320T144531Z.json`. Claims+mapping succeeded via configured `allenai/olmo-3.1-32b-instruct`; Lean call returned HTTP 404 on `chat/completions` for this Lean model (provider route unavailable for account). |
| 2026-03-20 | agent | Live eval `math_sum_evens` with Lean override | `allenai/olmo-3.1-32b-instruct` | Report: `benchmarks/reports/llm_live_math_sum_evens_lean_olmo.json`. Claims+mapping succeeded; Lean reached provider but failed JSON extraction (`Invalid control character`), indicating non-strict JSON output from model response. |
| 2026-03-20 | agent | Live eval after error fixes | `allenai/olmo-3.1-32b-instruct` | Report: `benchmarks/reports/llm_live_math_sum_evens_after_error_fixes.json`. Claims/mapping/Lean all schema-valid (`ok: true`); Lean returned `proposal_count: 0` (valid empty suggestion set). |
| 2026-03-20 | agent | **Full E2E pipeline run** (`math_sum_evens`) | `allenai/olmo-3.1-32b-instruct` | Branch: `e2e-llm-pipeline-run`. **All LLM surfaces executed live:** claims (0 proposals, schema-valid), mapping (1 proposal applied via `--apply --i-understand-human-reviewed`), Lean (1 proposal generated, schema-valid). **Applied:** mapping merged into `mapping.json`. **Final gates:** Lean build passed, `validate-all` passed (warnings only), benchmark passed with `llm_prompt_templates` digests. Report: `benchmarks/reports/llm_live_e2e_math_sum_evens.json`. |
