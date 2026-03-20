# Metrics (SPEC Section 12)

This document maps each metric category from SPEC Section 12 to where the metric is produced or displayed. Use it to locate and evaluate product, formalization, extraction, infra, and research-value metrics.

---

## Product metrics

| Metric | Source / display |
|--------|------------------|
| Number of papers admitted | Portal dashboard; `corpus/index.json`; coverage dashboard totals |
| Number of claim bundles | Portal dashboard (Totals: Claims); aggregate from paper manifests |
| Percentage of claims with source spans | Derived from claims with valid `source_span`; coverage in manifest / dashboard |
| Percentage of claims mapped to formal targets | Dashboard "Mapped" vs "Claims"; `manifest.coverage_metrics.mapped_claim_count` |
| Percentage of mapped claims machine-checked | Dashboard "Machine-checked"; `manifest.coverage_metrics.machine_checked_count` |
| Percentage linked to executable kernels | Dashboard "Kernel-linked"; `manifest.coverage_metrics.kernel_linked_count` |
| Median time from paper intake to first artifact page | CLI: `uv run --project pipeline python -m sm_pipeline.cli metrics --median-intake-time` (uses `intake_report.json` created_at and metadata `first_artifact_at`). Papers without both are excluded. |

**Primary display:** [Portal coverage dashboard](/dashboard) (or `portal/app/dashboard/page.tsx`). Data comes from `corpus/papers/<paper_id>/manifest.json` and `coverage_metrics`.

---

## Formalization metrics

| Metric | Source / display |
|--------|------------------|
| Declaration compile rate, proof completion rate | Lean build (Lake); CI gate 1; proof completion rate and Milestone 3 progress via `just metrics --proof-completion`. |
| Axiom / sorry count (repo-level and per-paper) | CLI: `just metrics --axiom-count`; scans `formal/**/*.lean`; per-paper via mapping.json namespace. |
| Dependency reuse ratio | CLI: `metrics --dependency`; computed from manifest `dependency_graph` and theorem_cards `dependency_ids`. |
| Average theorem-card fan-in / fan-out | Same as above; report includes average_fan_in, average_fan_out, max_fan_in, max_fan_out. |
| Number of claims marked disputed after formalization | `just metrics --research-value`: `disputed_claims_with_formal_targets` (claims with `status: disputed` and non-empty `linked_formal_targets`) |

**Primary sources:** Lean build success (CI); `corpus/papers/<paper_id>/manifest.json` (theorem cards, dependency graph); `theorem_cards.json`.

---

## Extraction metrics

| Metric | Source / display |
|--------|------------------|
| Claim extraction precision/recall/F1, assumption precision/recall/F1 | Gold task in `just benchmark`; report keys `gold_claim_precision`, `gold_claim_recall`, `gold_claim_f1`, `gold_assumption_*`. See [Gold labels](#gold-labels-extraction-precisionrecall). |
| Symbol normalization conflict rate | CLI: `just metrics --symbol-conflict` (or `just metrics`); see Metrics CLI below. |
| Source-span alignment | For each claim id listed in `benchmarks/gold/<paper_id>/source_spans.json`, corpus `source_span` is compared to the reference. **Benchmark (Gate 6):** `tasks.gold` includes `source_span_total_compared`, `source_span_alignment_error_count`, and `source_span_alignment_error_rate` (same computation as the metrics CLI). **Regression:** `benchmarks/baseline_thresholds.json` may set `tasks_ceiling.gold.source_span_alignment_error_rate` (maximum allowed rate; 0 means no mismatches). **CLI duplicate:** `just metrics --source-span-alignment` emits `source_span_alignment` with `total_compared`, `alignment_error_count`, `alignment_error_rate`. See [Gold labels](#gold-labels-extraction-precisionrecall). |

**Primary source:** Benchmark suite. Run `just benchmark` (or `uv run --project pipeline python -m sm_pipeline.cli benchmark`). Results are written to `benchmarks/reports/latest.json` and include `proof_success_snapshot` (machine_checked_count, declaration_count, fraction_machine_checked); `tasks.theorem_cards.per_paper` (per-paper quality slices); `tasks.gold` (including source-span alignment fields above); `proof_success_summary.md`; and `benchmarks/reports/trend/proof_success_history.json` (rolling trend history). Gate 6 trend check: if fraction_machine_checked decreased vs previous run, a warning is written to the summary (warn-only). See also [Generated artifacts](generated-artifacts.md). The main PR validation workflow runs the benchmark with regression check (Gate 6), including runtime budgets, minimum thresholds under `tasks`, and optional ceilings under `tasks_ceiling`; extraction/proof metrics are enforced before merge.

---

## Infra metrics

| Metric | Source / display |
|--------|------------------|
| Cold build time, cached build time, portal build time | CI job timings; local `time just build` / `time pnpm --dir portal build` |
| Flaky test rate, schema migration break rate | CI history; manual tracking; test runs in GitHub Actions |

**Primary source:** GitHub Actions workflow run durations and logs; local timing of `just build`, `just validate`, and portal build.

**Optional automation (report-only):** Workflow jobs can record pass/fail per job to a JSON artifact; compare consecutive runs manually or via the [GitHub Actions API](https://docs.github.com/en/rest/actions/workflow-runs). Full flaky-rate dashboards are not required for v0.2; document counts from Actions run history when auditing infra health.

---

## Research-value metrics

| Metric | Source / display |
|--------|------------------|
| Reusable foundation count, cross-paper reuse count | CLI: `just metrics --research-value`; from manifest dependency_graph and theorem_cards. |
| Literature error discoveries | Same CLI; from `corpus/papers/<paper_id>/literature_errors.json` when present (schema: literature_error.schema.json); else ADR placeholder count. |
| Claims whose assumptions were clarified | Same report: `claims_with_clarified_assumptions` (claims with non-empty `linked_assumptions`). |
| Kernels with formally linked invariants | Same report: `kernels_with_formally_linked_invariants` (kernels in `corpus/kernels.json` with non-empty `linked_theorem_cards`). |
| Disputed claims still linked to formal targets | Same report: `disputed_claims_with_formal_targets` (reviewer workflow signal after formalization). |

**Primary sources:** `just metrics --research-value`; data contracts documented in `pipeline/src/sm_pipeline/metrics/research_value.py`.

---

## Gold labels (extraction precision/recall)

Extraction precision and recall use a **gold labelled** set of claims and assumptions per paper when present. Layout: `benchmarks/gold/<paper_id>/claims.json` and `assumptions.json`, same schema as corpus. The gold task (`benchmarks/tasks/gold/scorer.py`) runs via `just benchmark` and returns:

- **Counts:** `papers_with_gold`, `gold_claim_count`
- **Claim quality (when corpus and gold exist for same papers):** `gold_claim_precision`, `gold_claim_recall`, `gold_claim_f1`
- **Assumption quality (when both gold and corpus have assumptions):** `gold_assumption_precision`, `gold_assumption_recall`, `gold_assumption_f1`
- **Source-span alignment (when any `benchmarks/gold/<paper_id>/source_spans.json` exists):** `source_span_total_compared`, `source_span_alignment_error_count`, `source_span_alignment_error_rate` (via `sm_pipeline.metrics.source_span_alignment.compute_source_span_alignment`)

**Matching contract (deterministic):** Corpus and gold items are matched by `id`. True positives = ids present in both corpus and gold for that paper. Precision = TP / |corpus|, Recall = TP / |gold|, F1 = 2*P*R/(P+R). Aggregation is micro-averaged over all papers with gold. When no gold dirs exist, the task returns `papers_with_gold: 0`, `gold_claim_count: 0`. **This repository** sets `tasks.gold.papers_with_gold` to the number of papers in `corpus/index.json` and enforces gold F1 floors plus `tasks_ceiling.gold.source_span_alignment_error_rate`; forks may set `papers_with_gold` to 0 or omit ceilings while bootstrapping. **Ceilings:** `tasks_ceiling` holds upper bounds (e.g. `tasks_ceiling.gold.source_span_alignment_error_rate`). Gold dirs for all six indexed papers: `benchmarks/gold/` (`langmuir_1918_adsorption`, `freundlich_1906_adsorption`, `chem_dilution_reference`, `temkin_1941_adsorption`, `math_sum_evens`, `physics_kinematics_uniform`).

### Gold-creation workflow

**Process (state of the art):** For every **new** paper added to `corpus/index.json`, create `benchmarks/gold/<paper_id>/` with at least `claims.json` (and optionally `assumptions.json`, `source_spans.json`) as part of the intake or first-artifact workflow. This keeps the metrics gap as an ongoing process (add gold when admitting a paper), not a backlog.

1. **Choose paper:** Use a paper that has (or will have) corpus `claims.json` and optionally `assumptions.json`.
2. **Scaffold or create directory:** Run `just scaffold-gold <paper_id>` to create `benchmarks/gold/<paper_id>/` from the corpus (copies claims, builds `source_spans.json` from claim `source_span`, copies assumptions). Then curate as needed. Or create the directory and files by hand.
3. **Add gold labels:** Create or edit `claims.json` and/or `assumptions.json` with the same JSON schema as the corpus. Each item should have an `id`; matching is by `id` (corpus item matches gold if the id exists in gold; precision/recall are computed over matched counts).
4. **Optional source-span reference:** `scaffold-gold` writes `source_spans.json` when claims have `source_span`. Or add by hand: a list of `{ "claim_id": "<id>", "source_span": { ... } }`; used by gold task and `just metrics --source-span-alignment`.
5. **Run benchmark:** `just benchmark`; the report includes `gold_claim_*`, `gold_assumption_*` when applicable, and source-span alignment fields on `tasks.gold` when any gold `source_spans.json` exists. CI runs the benchmark on every PR. **Current state:** all six papers in `corpus/index.json` have gold (claims and `source_spans.json` where claims carry spans; assumptions copied when present in corpus). Add gold for each new paper before merging (see [paper-intake.md](paper-intake.md) and [ROADMAP.md](../ROADMAP.md)).

---

## Axiom count and research-value (instrumented)

| Metric | Source |
|--------|--------|
| Axiom / sorry count | CLI: `just metrics --axiom-count`. Scans `formal/**/*.lean` for word-boundary `axiom` and `sorry`; reports total, per-file, and per-paper (when mapping.json namespace maps files to papers). Best-effort (no full Lean AST). |
| Reusable foundation count, cross-paper reuse | CLI: `just metrics --research-value`. From manifests and theorem_cards: declarations used as dependency targets by more than one paper. |
| Literature errors | Same report: when `corpus/papers/<paper_id>/literature_errors.json` exists, count used; else ADR placeholder. |
| Claims with clarified assumptions | Same report: `claims_with_clarified_assumptions`. |
| Kernels with formally linked invariants | Same report: `kernels_with_formally_linked_invariants`. |

## Not yet instrumented

| Metric | What would be needed |
|--------|----------------------|
| Unit/dimension tagging automation | Schema has dimensional_metadata; `just metrics --dimension-visibility` and `just metrics --dimension-suggestions` (heuristic suggestions for human triage); no automatic corpus edit. |

---

## Metrics CLI

Run all derived metrics or specific ones (from repo root):

```bash
just metrics
just metrics -o report.json
# Or with flags: uv run --project pipeline python -m sm_pipeline.cli metrics --median-intake-time --dependency --symbol-conflict -o report.json
```

- **Median intake time:** Requires `intake_report.json` (created_at) and metadata `first_artifact_at` per paper.
- **Dependency:** Reads `manifest.json` dependency_graph or theorem_cards dependency_ids; outputs reuse ratio, fan-in, fan-out.
- **Symbol conflict:** Reads each paper's `symbols.json`; outputs per-paper and aggregate conflict rate.
- **Proof completion:** Reads all manifests' coverage_metrics; outputs proof_completion_rate and Milestone 3 progress (see manifest totals; target in docs was 20–40 machine-checked claims).
- **Normalization report:** Cross-paper duplicate `normalized_name` report (8.3 visibility); includes `suggest_merge` for human triage; `--normalization-report` or included in default run.
- **Axiom count:** Scans `formal/**/*.lean` for `axiom` and `sorry`; `--axiom-count`.
- **Research-value:** Reusable foundation, cross-paper reuse, literature_errors count (from optional literature_errors.json or ADR placeholder); `--research-value`.
- **Source-span alignment:** When `benchmarks/gold/*/source_spans.json` exists; `--source-span-alignment`.
- **Normalization visibility (8.3):** Symbols with role_unclear, claims without linked_assumptions; `--normalization-visibility`.
- **Assumption suggestions (8.3):** Candidate assumptions for claims with none (text overlap); `--assumption-suggestions`; human triage only.
- **Dimension visibility (8.3):** Symbols with vs without dimensional_metadata; `--dimension-visibility`.
- **Dimension suggestions (8.3):** Heuristic suggested unit/dimension for symbols (from kernels and symbol names); `--dimension-suggestions`; human triage only, no corpus auto-edit.
- **Normalization policy (8.3):** Waiver-backed policy checks; `--normalization-policy`. Reads `benchmarks/normalization_policy.json`; reports unwaived cross-paper duplicates, assumption coverage, and dimension violations; warn-only unless CI promotes to fail.
- **Reviewer status:** Theorem-card reviewer queues and consistency checks; emitted as `reviewer_status` in `just metrics` output.

---

## Quick reference

- **Dashboard (product coverage):** Portal `/dashboard`; data from paper manifests.
- **Derived metrics:** Run `just metrics` (or `uv run --project pipeline python -m sm_pipeline.cli metrics`); optional `-o report.json`.
- **Extraction / proof metrics:** Run `just benchmark`; see `benchmarks/reports/` (e.g. `latest.json`).
- **Formalization health:** Lean build in CI (gate 1); Lake and theorem cards for structure.
- **Infra health:** CI run times and test results in GitHub Actions.
