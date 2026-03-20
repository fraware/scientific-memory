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

## Schemas and models

Schema changes require updates in lockstep per project rules: JSON schema under `schemas/`, Pydantic models under `pipeline/src/sm_pipeline/models/`, fixtures under `schemas/examples/`, and notes in [Schema versioning and migration notes](contributor-playbook.md#schema-versioning-and-migration-notes).

## Blueprints and leanblueprint (deferred, SPEC 8.4)

[blueprint/](../blueprint/) and [blueprints/](blueprints/) are narrative and structural docs today. Integration with the **leanblueprint** ecosystem (auto-generated dependency graphs from Lean) is **deferred**: not required for merge gates.

Until then:

- **Authoritative mapping:** `corpus/papers/<paper_id>/mapping.json` and Lean sources under `formal/`.
- **Check:** `sm-pipeline check-paper-blueprint <paper_id>` compares blueprint markdown to mapping when present.

When leanblueprint is adopted, update this section and an ADR as needed.
