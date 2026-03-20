# Pipeline extension points

How to extend ingestion, extraction, or publication without forking the monolith.

## Orchestration registry

Stage execution for SPEC 8.x flows is centralized in [`pipeline/src/sm_pipeline/pipeline_orchestrator.py`](../pipeline/src/sm_pipeline/pipeline_orchestrator.py).

- **Default behavior:** `run_pipeline_for_paper` runs selected [`PipelineStage`](../pipeline/src/sm_pipeline/models/stage_contracts.py) values in order using built-in handlers.
- **Overrides:** Call `register_pipeline_stage_handler(stage, handler)` to substitute a stage implementation (for example in tests or a downstream plugin package that vendors `sm_pipeline`). Use `reset_pipeline_stage_handlers()` in test teardown to restore defaults.

Handlers must have the signature:

```python
def handler(repo_root: Path, paper_id: str) -> StageOutcome: ...
```

Stages that remain **manual by design** (`formalization`, `kernel_linkage`) still emit `skipped` outcomes from the orchestrator; they are not registered handlers.

## Publication

- **Single path:** Use [`sm_pipeline.publish.canonical.publish_paper_artifacts`](../pipeline/src/sm_pipeline/publish/canonical.py) whenever you regenerate one paper’s published JSON so `portal/.generated/corpus-export.json` is refreshed consistently.
- **Portal bundle shape:** Only [`build_portal_bundle`](../pipeline/src/sm_pipeline/publish/portal_read_model.py) defines the export structure; the CLI writes it via [`export_portal_data`](../pipeline/src/sm_pipeline/publish/export_portal_data.py).

## Validation

- Add new invariant checks by extending the gate engine in [`validate/gate_engine.py`](../pipeline/src/sm_pipeline/validate/gate_engine.py) rather than ad hoc scripts, so `validate-all` and `--report-json` stay authoritative.

## Optional LLM proposals (Prime Intellect)

- **Provider code:** [`pipeline/src/sm_pipeline/llm/`](../pipeline/src/sm_pipeline/llm/) (`LLMProvider` protocol, Prime Intellect HTTP adapter).
- **CLI:** `sm-pipeline llm-claim-proposals`, `llm-mapping-proposals`, `llm-lean-proposals`, `llm-lean-proposals-to-apply-bundle`, `llm-apply-*` (see [prime-intellect-llm.md](prime-intellect-llm.md)).
- **Extension pattern:** wrap `run_extraction_stage` or add a local script that calls proposal generators; do not auto-apply in CI. Prefer `register_pipeline_stage_handler` only if the substituted handler remains deterministic or is explicitly opt-in via environment flags.
- **Sidecar validation:** [`validate/llm_proposals.py`](../pipeline/src/sm_pipeline/validate/llm_proposals.py) is **warn-only** when suggestion sidecars (`llm_claim_proposals.json`, `llm_mapping_proposals.json`, `llm_lean_proposals.json`, `suggested_*.json`) exist under a paper directory.
- **Eval / regression:** Prompt literals and template digests live in [`llm/prompt_templates.py`](../pipeline/src/sm_pipeline/llm/prompt_templates.py). Reviewed reference bundles under [`benchmarks/llm_eval/`](../benchmarks/llm_eval/README.md) are scored by benchmark task `llm_eval`; `just benchmark` also emits top-level `llm_prompt_templates`. See [ADR 0013](adr/0013-llm-evaluation-policy.md).
- **Publish escape hatch:** set `SM_PUBLISH_REUSE_MANIFEST_GRAPHS=1` only if you intentionally need to preserve prior manifest `dependency_graph` / `kernel_index` (default is fresh recompute each publish).

## Schemas and models

Schema changes require updates in lockstep per project rules: JSON schema under `schemas/`, Pydantic models under `pipeline/src/sm_pipeline/models/`, fixtures under `schemas/examples/`, and notes in [Schema versioning and migration notes](contributor-playbook.md#schema-versioning-and-migration-notes).

## Blueprints and leanblueprint (deferred, SPEC 8.4)

[blueprint/](../blueprint/) and [blueprints/](blueprints/) are narrative and structural docs today. Integration with the **leanblueprint** ecosystem (auto-generated dependency graphs from Lean) is **deferred**: not required for merge gates.

Until then:

- **Authoritative mapping:** `corpus/papers/<paper_id>/mapping.json` and Lean sources under `formal/`.
- **Check:** `sm-pipeline check-paper-blueprint <paper_id>` compares blueprint markdown to mapping when present.

When leanblueprint is adopted, update this section and an ADR as needed.
