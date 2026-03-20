# Playbook: Reviewer

Clean-clone smoke: [CONTRIBUTING.md](../../CONTRIBUTING.md), `scripts/contributor_dry_run.sh`.

For contributors who review pull requests. Use this track to verify artifact impact, provenance, and gates so PRs can be approved with confidence.

## Prerequisites

- Local setup: `just bootstrap`, `just build`. Run `just validate` and `just test` to confirm the branch is in a good state before reviewing.

## Gate checklist (before approving a PR)

1. **Validate**  
   `just validate` passes (runs [`gate_engine`](../../pipeline/src/sm_pipeline/validate/gate_engine.py): schema, normalization, provenance, graph integrity, coverage, extraction_run requirement, migration doc if schemas changed, snapshot-quality warnings). Optional: `validate-all --report-json /tmp/gate-report.json` after a green run for a machine-readable checklist.

2. **Tests and build**  
   `just test` and `just build` (Lean + portal + pipeline) pass.

3. **Reviewer workflow**  
   No claim has `status: "disputed"` without non-empty `review_notes`. No invalid claim status values (see [Reviewer guide](../contributor-playbook.md#reviewer-guide) for allowed statuses).

4. **Artifact impact**  
   PR description states what changed: papers, claims, declarations, kernels, or portal routes. New or edited claims have `source_span`; new declarations are in the paper’s mapping.

5. **Red flags**  
   See [Reviewer guide – Red flags](../contributor-playbook.md#red-flags). Block on: claim without source_span, declaration not in mapping, hand-edited manifest coverage, dangling theorem-card or kernel refs, schema change without migration note, paper with claims but no `extraction_run.json`.

## End-to-end path (review a PR)

1. **Checkout and run gates**  
   Check out the PR branch. Run `just validate`, `just test`, `just build`. If any fail, request changes and point to the failing gate or [troubleshooting](#failure-troubleshooting) below.

2. **Reviewer report (optional)**  
   Run `just metrics` (or `uv run --project pipeline python -m sm_pipeline.cli metrics --reviewer-report -o report.json`). Check `reviewer_report` for disputed claims without notes or invalid statuses.

3. **Content review**  
   For corpus/formal changes: confirm claims have source spans, mapping matches declarations, and manifest/coverage were regenerated (not hand-edited). For schema changes: confirm [Schema versioning and migration notes](../contributor-playbook.md#schema-versioning-and-migration-notes) has a migration entry.

4. **Approve or request changes**  
   If all gates pass and no red flags: approve. Otherwise list blocking issues and suggest fixes (e.g. “Add source_span to claim X”, “Run just publish-artifacts <paper_id>”).

## Failure troubleshooting

| Failure | What to request |
|--------|----------------|
| Schema validation | Author to fix the reported file per `schemas/`; add migration note if schema changed. |
| Normalization | Author to fix duplicate IDs or broken linked_assumptions/linked_symbols. |
| Provenance | Author to add source_span to claims or add declarations to mapping / remove stray declarations. |
| Graph integrity | Author to fix dangling theorem_card or kernel references (IDs must exist in corpus). |
| Coverage | Author to run `just publish-artifacts <paper_id>` and not edit manifest coverage by hand. |
| extraction_run missing | Author to run `just extraction-report <paper_id>` or add `extraction_run.json` for papers with claims. |
| Migration doc | Author to add a note under **Migration notes** in [Schema versioning and migration notes](../contributor-playbook.md#schema-versioning-and-migration-notes). |
| Disputed without notes | Author to add `review_notes` to the disputed claim or change status. |

## Quick reference

| Goal | Command |
|------|---------|
| Validate | `just validate` |
| Test | `just test` |
| Build | `just build` |
| Reviewer report | `just metrics` (includes reviewer_report in full output) |
| Reviewer guide | [Contributor playbook – Reviewer guide](../contributor-playbook.md#reviewer-guide) |
