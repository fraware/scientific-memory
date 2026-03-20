# Paper intake (SPEC 8.1)

SPEC 8.1 requires: paper metadata validated; **source hash stored**; **reproducible ingestion command exists**. This document describes how the project satisfies these acceptance criteria.

## Reproducible ingestion command

The reproducible ingestion flow is:

1. **Admit the paper**
   ```bash
   just add-paper <paper_id>
   ```
   This creates `corpus/papers/<paper_id>/` with initial `metadata.json`, `claims.json`, `assumptions.json`, `symbols.json`, `mapping.json`, and `manifest.json`. An optional `intake_report.json` (paper_id, created_at, source_files_found) is written as a minimal "initial parsing report"; see [Generated artifacts](generated-artifacts.md). Use a stable paper ID (e.g. `author_year_topic`). Set `domain` in `metadata.json` to a schema-allowed value (see [Domain policy](contributor-playbook.md#domain-policy)). If you have a DOI or arXiv ID, set `metadata.source.doi` or `metadata.source.arxiv_id` (see [Contributor playbook](contributor-playbook.md)).

2. **Place source assets (optional)**
   Source files (PDF, LaTeX, etc.) may be placed under the paper directory in a documented location (e.g. `corpus/papers/<paper_id>/source/`). For optional pandoc-based extraction, use `corpus/papers/<paper_id>/source/main.tex`; then run `just extract-from-source <paper_id>` to generate `suggested_claims.json` (section headings plus candidate_equations, candidate_symbols, and macro_context from preamble) for human review (requires pandoc; see [pandoc-latex-integration.md](pandoc-latex-integration.md)). The exact path is not enforced by schema in v0.1.

3. **Extract claims and scaffold formal mapping**
   ```bash
   just extract-claims <paper_id>
   just scaffold-formal <paper_id>
   ```
   `extract-claims` supports `--mode scaffold_only` (default), `deterministic`, or `llm_sidecar`. In `scaffold_only`, a placeholder claim is written when `claims.json` is missing or `[]`. The other modes do not scaffold; use them when claims come from manual intake or LLM sidecars. Example: `uv run --project pipeline python -m sm_pipeline.cli extract-claims --paper-id <paper_id> --mode deterministic` (see [trust-boundary-and-extraction.md](trust-boundary-and-extraction.md)).

   Then edit claims, assumptions, and mapping as needed. For papers with non-empty `claims.json`, **`extraction_run.json` is required** (validation fails otherwise). Run `just extraction-report <paper_id>` to create or refresh it.

   Optional LLM assist (proposal sidecars only): [prime-intellect-llm.md](prime-intellect-llm.md) (`just llm-claim-proposals`, `just llm-mapping-proposals`, `just llm-lean-proposals` after mapping/Lean context exists; human-gated apply; Lean suggestions convert to `proof-repair-apply`).

4. **Publish artifacts**
   ```bash
   just publish-artifacts <paper_id>
   ```

5. **Add gold (required before merge for indexed papers)**  
   Run `just scaffold-gold <paper_id>` to create `benchmarks/gold/<paper_id>/` from the corpus (claims, `source_spans.json` from claim `source_span`, assumptions when present); then curate as needed. Update `benchmarks/baseline_thresholds.json` (`tasks.gold.papers_with_gold` and any related floors) when the corpus paper count changes. See [Metrics](metrics.md)#gold-labels-extraction-precisionrecall.

## Batch admit (multiple paper IDs)

For a CSV of upcoming papers (columns `paper_id`, `domain`; optional `title`, `year`):

```bash
uv run --project pipeline python -m sm_pipeline.cli batch-admit path/to/papers.csv
```

Each row runs the same skeleton as `just add-paper` when the directory is missing; existing rows update `metadata.json` domain/title/year. Rebuilds `corpus/index.json`. Human review of claims and formalization still required per paper.

The sequence above is the **reproducible ingestion command**: any contributor can run it from a clone to create or update a paper in the corpus. See [Contributor playbook](contributor-playbook.md) for the full workflow.

## Source hash

In v0.1, **source hash** is satisfied by:

- **Version control:** The corpus is under git; the commit hash (and optionally diff baselines under `corpus/snapshots/*.json`, including `last-release.json`, plus release checksums) provides integrity of the entire tree.
- **Per-paper source hashes:** Run `just hash-source <paper_id>` (or `just hash-source` for all papers) to compute and store SHA-256 hashes of paper source files; hashes are written under the paper directory for reproducibility. The admit flow can call this automatically.
- **Corpus index:** Run `just build-index` to regenerate `corpus/index.json` from paper metadata; the index is used by the portal and export. It is rebuilt as part of the intake automation when admitting a paper.

Acceptance criterion: *source hash stored* is met by version control, optional per-paper hash-source output, and release checksums (see [Release integrity (Gate 7)](contributor-playbook.md#release-integrity-gate-7)).

## Optional `metadata.yaml` (not used by pipeline)

Canonical paper metadata is **`metadata.json`** (validated by `paper.schema.json`). An optional **`metadata.yaml`** beside it is **not** read by the pipeline in v0.2.

If a future tool ingests YAML, the contract is: migrate YAML to JSON on admit (or treat YAML as a generator input only); the committed source of truth remains JSON so `validate-all` and the portal stay single-source. No workflow change is required for contributors today.

## Output naming (SPEC 8.1)

SPEC 8.1 lists output as `metadata.yaml`, normalized source assets, and initial parsing report. This project uses **JSON** for all corpus and manifest artifacts per [ADR 0004](adr/0004-json-storage.md): `metadata.json`, `claims.json`, and so on. The **initial parsing report** acceptance criterion is satisfied by the optional `intake_report.json` (paper_id, created_at, source_files_found) written on admit; see [Generated artifacts](generated-artifacts.md).
