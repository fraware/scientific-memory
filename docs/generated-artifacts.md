# Generated artifacts (SPEC 10.4)

Any generated file committed to the repository must be reproducible. This document lists artifacts and regeneration commands.

| Artifact | Generator command | Notes |
|---|---|---|
| `corpus/index.json` | `just build-index` | Rebuilt from paper metadata; used by pipeline/export/portal. |
| `corpus/papers/<paper_id>/metadata.json` (initial) | `just add-paper <paper_id>` | Initial scaffold at admission. |
| `corpus/papers/<paper_id>/claims.json` (template) | `just extract-claims <paper_id>` | Writes placeholder only when missing/empty. |
| `corpus/papers/<paper_id>/assumptions.json`, `symbols.json` (initial) | `just add-paper <paper_id>` | Initial empty arrays when missing. |
| `corpus/papers/<paper_id>/mapping.json` | `just scaffold-formal <paper_id>` or `just generate-mapping <paper_id>` | Scaffold or derive claim-to-declaration map. |
| `corpus/papers/<paper_id>/theorem_cards.json` | `just publish-artifacts <paper_id>` | Derived from claims + mapping; dependency_ids from Lean source extraction; executable_links from corpus/kernels.json. |
| `corpus/papers/<paper_id>/manifest.json` | `just publish-artifacts <paper_id>` | Coverage, pages, declaration index, `dependency_graph` and `kernel_index` (recomputed each publish unless `SM_PUBLISH_REUSE_MANIFEST_GRAPHS=1`), `build_hash` / `build_hash_version` (v2 content-addressed when `claims.json` exists). |
| `corpus/papers/<paper_id>/normalization_report.json` | `just normalize-paper <paper_id>` | Duplicate normalized symbols and unresolved-link summary. |
| `corpus/papers/<paper_id>/intake_report.json` | `just add-paper <paper_id>` or `just intake-report <paper_id>` | **Initial parsing report (SPEC 8.1):** intake timestamp and source-files found. |
| `corpus/papers/<paper_id>/extraction_run.json` | `just extract-claims <paper_id>` or `just extraction-report <paper_id>` | Extraction run summary metrics; may include `extraction_mode` and `placeholder_claim_written` when produced by `extract-claims`. **Required** for papers with non-empty claims (validation enforces). |
| `corpus/snapshots/<baseline-id>.json` (default `last-release.json`) | `just export-diff-baseline` or `sm-pipeline export-diff-baseline --baseline-id <id>` | Baseline snapshot(s) for portal diff page; supports title/narrative metadata. **Naming:** Use `v{semver}-corpus.json` or `release-{tag}.json` aligned with git tags; keep `last-release.json` as canonical current alias. Release baselines require non-empty `title`, `narrative` (min 10 chars), and `highlights` array (see [release-policy.md](../infra/release-policy.md)). |
| `corpus/kernels.json` | hand-maintained | Canonical kernel index validated by schema/graph checks. |
| `portal/.generated/corpus-export.json` | `just export-portal-data` | Canonical bundle for portal consumption; built via `sm_pipeline.publish.portal_read_model.build_portal_bundle`. |
| `docs/status/repo-snapshot.md` | `just repo-snapshot` | Generated table from each paper's `manifest.json`: machine-checked count, `build_hash_version`, and dependency-graph edge count (avoid duplicating numbers in SPEC). |
| `docs/verso/_build/` (HTML site) | `just build-verso` or `lake exe generate-site` | Verso manual output from [scripts/verso/](../scripts/verso/); directory is gitignored. Not a CI gate. See [Contributor playbook – Verso](contributor-playbook.md#verso-integration-optional). |
| `benchmarks/reports/latest.json` | `just benchmark` | Benchmark report (includes `proof_success_snapshot`, task `per_paper` quality slices, `tasks.gold` with extraction F1 and source-span alignment fields, `tasks.llm_suggestions`, `tasks.llm_lean_suggestions`, `tasks.llm_eval` for `benchmarks/llm_eval/` reference bundles, and top-level `llm_prompt_templates` digests); compared against `baseline_thresholds.json` (`tasks` and `tasks_ceiling`). |
| `benchmarks/reports/proof_success_summary.md` | `just benchmark` | Proof success summary (machine_checked, declarations, fraction); includes Gate 6 trend warning if fraction dropped. |
| `benchmarks/reports/trend/proof_success_history.json` | `just benchmark` | Rolling history of proof_success snapshots (timestamp, counts, fraction); cap at 100 entries; used for trend checks. |
| `benchmarks/gold/<paper_id>/...` | `just scaffold-gold <paper_id>` then curate | Gold labels and `source_spans.json` for extraction metrics and Gate 6 alignment; required for each paper listed in `corpus/index.json` under current baseline (`papers_with_gold`). |
| `dist/CHANGELOG.md`, `dist/checksums.txt` | `scripts/release_artifacts.sh` | Release integrity artifacts. Git log section first; `scripts/release_corpus_delta.py` (when `uv` is available) appends a structured corpus/formal/kernel **release delta** block to `dist/CHANGELOG.md`. |
| `dist/checksums.txt.sig`, `dist/checksums.txt.pem` | Release workflow (cosign) | Sigstore keyless signature and certificate for checksums.txt. |
| `dist/release-bundle.zip` | Release workflow (after packaging) | Zip of full `dist/`; uploaded to GitHub Release with tag. |
| `benchmarks/normalization_policy.json` | hand-maintained (optional) | Waiver and coverage targets for `just metrics --normalization-policy`. |
| Proof-repair proposal JSON | `sm-pipeline proof-repair-proposals -o <path>` | Human-review-only artifact; schema `proof_repair_proposal.schema.json`. Never auto-applied. |
| `corpus/papers/<paper_id>/llm_claim_proposals.json` | `sm-pipeline llm-claim-proposals --paper-id <paper_id>` | Optional LLM suggestion bundle (`llm_claim_proposals.schema.json`); `verification_boundary: human_review_only`. Review before `llm-apply-claim-proposals`. |
| `corpus/papers/<paper_id>/llm_mapping_proposals.json` | `sm-pipeline llm-mapping-proposals --paper-id <paper_id>` | Optional mapping suggestions (`llm_mapping_proposals.schema.json`). Review before `llm-apply-mapping-proposals`. |
| `corpus/papers/<paper_id>/llm_lean_proposals.json` | `sm-pipeline llm-lean-proposals --paper-id <paper_id>` | Optional surgical Lean find/replace suggestions (`llm_lean_proposals.schema.json`). Convert with `llm-lean-proposals-to-apply-bundle`, then human-gated `proof-repair-apply` (never auto-applied). |
| `corpus/papers/<paper_id>/suggested_assumptions.json` | Human or LLM (no default generator) | Non-canonical assumption suggestions (`suggested_assumptions.schema.json`); validate-all warns if invalid. |
| `corpus/papers/<paper_id>/suggested_symbols.json` | Human or LLM (no default generator) | Non-canonical symbol suggestions (`suggested_symbols.schema.json`). |
| `corpus/papers/<paper_id>/suggested_mapping.json` | Human or LLM (no default generator) | Non-canonical mapping suggestions (`suggested_mapping.schema.json`). |
| `schemas/llm_run_provenance.schema.json` | — | Reusable provenance shape for LLM/suggestion bundles (`metadata` on proposal files). |
| Proof-repair apply bundle (optional, local) | Human-authored from reviewed proposals | Schema `proof_repair_apply_bundle.schema.json`; consumed only by `proof-repair-apply` (not generated by default). |
| (optional) Gate report JSON | `uv run --project pipeline python -m sm_pipeline.cli validate-all --report-json <path>` | Written only after a **successful** validation; describes checks run by [`gate_engine`](../pipeline/src/sm_pipeline/validate/gate_engine.py). Not committed by default. |

## Verification and policy

- Release workflow runs `scripts/verify_release_checksums.sh` after packaging, signs `dist/checksums.txt` with Sigstore (cosign), zips `dist/` as `release-bundle.zip`, and publishes a GitHub Release with those assets.
- Do not hand-edit `manifest.json`; regenerate via `just publish-artifacts <paper_id>`.
- Papers with claims must have `extraction_run.json` (run `just extraction-report <paper_id>` if missing).
- Update this document when generator commands or generated files change.
