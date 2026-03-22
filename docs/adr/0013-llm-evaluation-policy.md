# ADR 0013: LLM evaluation policy (fixtures, benchmarks, human rubric)

## Status

Accepted

## Context

Optional LLM proposal sidecars ([ADR 0011](0011-llm-worker-suggest-only.md)) need reproducible engineering signals: prompt versioning, offline regression anchors, benchmark-visible quality proxies, and documented human review—without treating model output as canonical.

## Decision

1. **Prompt templates** live in [`pipeline/src/sm_pipeline/llm/prompt_templates.py`](../../pipeline/src/sm_pipeline/llm/prompt_templates.py). Each generation run records `metadata.prompt_template_id`, `metadata.prompt_template_sha256`, and `metadata.input_artifact_sha256` (per-input SHA-256 of serialized inputs).
2. **Reference fixtures** under `benchmarks/llm_eval/<paper_id>/` (`reference_llm_*_proposals.json`) are reviewed, non-canonical anchors scored by the `llm_eval` benchmark task.
3. **Benchmark reports** include `llm_prompt_templates` (declared template id → digest map) alongside `tasks.llm_eval`.
4. **Human rubric** for semantic review is [`docs/testing/llm-human-eval-rubric.md`](../testing/llm-human-eval-rubric.md).
5. **Optional operator scripts:** [`scripts/llm_live_eval.py`](../../scripts/llm_live_eval.py) (smoke/live JSON report), [`scripts/llm_eval_lean_build_optional.py`](../../scripts/llm_eval_lean_build_optional.py) when `LLM_EVAL_RUN_LAKE_BUILD=1`; `just llm-live-eval`, `just llm-eval-lean-build-optional`.

## Consequences

- Changing prompt text bumps template digests; reviewers update reference fixtures when expectations change.
- `tasks.llm_eval` minima in `benchmarks/baseline_thresholds.json` guard fixture presence and proxy metrics; they do not prove model quality on unseen papers.
- Live API evaluation remains optional and out of default PR CI; deterministic tests and fixtures stay PR-blocking.

## Links

- [prime-intellect-llm.md](../tooling/prime-intellect-llm.md)
- [metrics.md](../metrics.md) (extraction / benchmark sections)
- [llm-lean-live-test-matrix.md](../testing/llm-lean-live-test-matrix.md)
