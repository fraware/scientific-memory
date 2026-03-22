# Playbook: Domain expander

For contributors who add papers in a **new domain** (e.g. first mathematics or physics paper). Ensures the new domain passes the full pipeline and CI.

## Prerequisites

- One-time setup: `just bootstrap`, `just build`. See [Contributor playbook](../contributor-playbook.md).
- For **hard-dimension stress** admissions (units, asymptotics, etc.), declare `tags` / `hardness` rationale in `metadata.json` and read [Hard-wedge stress papers](../operations/hard-wedge-stress-papers.md).

## Gate checklist (before opening a PR)

1. **Domain in schema**  
   The paper’s `metadata.json` must use a `domain` value allowed in `schemas/paper.schema.json` (e.g. `chemistry`, `mathematics`, `physics`, `probability`, `control`, `quantum_information`, `other`). If the domain is new, add it to the schema and to the pipeline Paper model, and add a migration note in [Schema versioning and migration notes](../contributor-playbook.md#schema-versioning-and-migration-notes).

2. **Namespace under formal/**  
   Lean code for the new domain should live under a dedicated namespace (e.g. `ScientificMemory.Mathematics.*`). Add the new module(s) to `formal/ScientificMemory/Index.lean`.

3. **Full pipeline**  
   The new paper must have: `metadata.json`, `claims.json`, `assumptions.json` (if any), `symbols.json`, `mapping.json`, `extraction_run.json` (required when the paper has non-empty claims), and after formalization `theorem_cards.json` and `manifest.json` generated via `just publish-artifacts <paper_id>`.

4. **Validate and build**  
   `just validate` and `lake build` (or `just build`) pass. No dangling references; coverage and provenance intact.

5. **Benchmark baseline**  
   If the new paper adds claims/declarations, update `benchmarks/baseline_thresholds.json` so Gate 6 regression check still passes (e.g. increase `paper_count`, `claim_count`, `declaration_count`, `machine_checked_count` as needed).

## End-to-end path (add a new domain slice)

1. **Add paper and corpus**  
   `just add-paper <paper_id>`. Set `domain` in `metadata.json` to the desired value (add to schema first if new). Edit `claims.json`, `assumptions.json`, `symbols.json` as needed. Run `just extract-claims <paper_id>` and ensure `extraction_run.json` exists (run `just extraction-report <paper_id>` if missing).

2. **Mapping and Lean**  
   `just scaffold-formal <paper_id>`. Edit `mapping.json`: set `namespace` to the new domain namespace (e.g. `ScientificMemory.Mathematics.MyPaper`), fill `claim_to_decl`. Create Lean file(s) under `formal/ScientificMemory/<Domain>/...` and add `import` in `formal/ScientificMemory/Index.lean`. Implement declarations so they compile (and proofs if applicable).

3. **Index and artifacts**  
   Add the paper to `corpus/index.json` (or run `just build-index` if the repo rebuilds index from metadata). Run `just publish-artifacts <paper_id>`.

4. **Validate and baseline**  
   `just validate`; fix any errors. Run `just benchmark` and, if thresholds fail, update `benchmarks/baseline_thresholds.json` with the new counts.

5. **Pre-PR**  
   `just check`. Optionally add a short blueprint in `docs/blueprints/<paper_id>.md` and extend [Domain policy](../contributor-playbook.md#domain-policy) in the contributor playbook if needed.

## Failure troubleshooting

| Failure | What to do |
|--------|------------|
| Domain not in schema | Add the domain to `schemas/paper.schema.json` enum and to `pipeline/src/sm_pipeline/models/paper.py`; add migration note in [Schema versioning and migration notes](../contributor-playbook.md#schema-versioning-and-migration-notes). |
| Lean build (unknown namespace) | Add `import ScientificMemory.<Domain>.<Module>` in `formal/ScientificMemory/Index.lean`. |
| extraction_run required | Run `just extraction-report <paper_id>` to create `extraction_run.json`. |
| Benchmark regression | Update `benchmarks/baseline_thresholds.json` to reflect the new paper/claim/declaration counts. |
| Graph integrity | Ensure theorem_cards and kernel links reference existing IDs; run `just publish-artifacts <paper_id>` again. |

## Quick reference

| Goal | Command |
|------|---------|
| Add paper | `just add-paper <paper_id>` |
| Build index | `just build-index` |
| Publish artifacts | `just publish-artifacts <paper_id>` |
| Validate | `just validate` |
| Benchmark | `just benchmark` |
| Domain policy | [Contributor playbook – Domain policy](../contributor-playbook.md#domain-policy) |
