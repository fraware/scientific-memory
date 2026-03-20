# Playbook: Formalizer

For contributors who add or extend Lean formalizations and link them to corpus claims. Follow this track end-to-end so CI passes without maintainer help.

## Prerequisites

- One-time setup from [Contributor playbook](../contributor-playbook.md): `just bootstrap`, `just build`, `just portal` (optional). Run `just doctor` if any step fails.

## Gate checklist (before opening a PR)

1. **Schema and normalization**  
   `just validate` must pass. Ensure:
   - Every claim has `source_span`; claim/assumption/symbol IDs are unique per paper; `linked_assumptions` and `linked_symbols` resolve to existing IDs.

2. **Provenance (Gate 3)**  
   Every declaration in the paper’s manifest must be reachable from a claim via `mapping.json`’s `claim_to_decl`. No hand-edited coverage in `manifest.json`.

3. **Lean build**  
   `lake build` (or `just build`) must succeed. New or edited `.lean` files must live under `formal/` and be imported from `ScientificMemory/Index.lean` if they belong to the main build.

4. **Publish artifacts**  
   After changing claims or mapping, run `just publish-artifacts <paper_id>` so `theorem_cards.json` and `manifest.json` are regenerated (including `dependency_ids` and `dependency_graph`). If you applied human-gated `proof-repair-apply` changes under `formal/`, republish affected papers and pass full CI (see [Verification boundary](../contributor-playbook.md#verification-boundary)).

5. **Full check**  
   `just check` (fmt, lint, validate, test, build). All must pass.

## End-to-end path (add or extend formalization)

1. **Paper and mapping**  
   If the paper is new: `just add-paper <paper_id>`, `just extract-claims <paper_id>`, `just scaffold-formal <paper_id>`.  
   Edit `corpus/papers/<paper_id>/claims.json` (source_span, informal_text, claim_type, status) and `mapping.json` (claim_to_decl: claim_id -> Lean declaration name).

2. **Lean code**  
   Add or edit files under `formal/ScientificMemory/...` so the declarations in `claim_to_decl` exist and compile. Use the namespace in `mapping.json` (e.g. `ScientificMemory.Chemistry.Adsorption.Langmuir1918`). If adding a new module, add an `import` in `formal/ScientificMemory/Index.lean`.

3. **Validation and artifacts**  
   `just check-paper <paper_id>` (runs full validate). Fix any schema/normalization/provenance/coverage errors. Then `just publish-artifacts <paper_id>`.

4. **Pre-PR**  
   `just check`. Fix any benchmark regression (see [Contributor playbook – When validation or benchmarks fail](../contributor-playbook.md#when-validation-or-benchmarks-fail)).

## Failure troubleshooting

| Failure | What to do |
|--------|------------|
| Schema validation error | Check the reported file against `schemas/*.schema.json`; add missing required fields, fix types. |
| Normalization (duplicate ID or broken link) | Deduplicate IDs per paper; ensure every `linked_assumptions` / `linked_symbols` entry exists in that paper’s assumptions/symbols. |
| Provenance (declaration not linked) | Add the declaration to `mapping.json`’s `claim_to_decl` for a claim, or remove the declaration from the Lean file if it is not intended to be in the manifest. |
| Coverage mismatch | Run `just publish-artifacts <paper_id>`; do not edit `manifest.json` coverage by hand. |
| Lean build failure | Fix the reported `.lean` error (e.g. missing import, type error). Use `just lake-build-verbose LOG=lake-build.log` for full output. |
| Benchmark regression | Ensure extraction/mapping/theorem_cards counts did not drop; if intentional, baseline may need a team-agreed update in `benchmarks/baseline_thresholds.json`. |

## Quick reference

| Goal | Command |
|------|---------|
| Scaffold mapping | `just scaffold-formal <paper_id>` |
| Check one paper | `just check-paper <paper_id>` (runs full validate) |
| Regenerate theorem cards and manifest | `just publish-artifacts <paper_id>` |
| Full pre-PR check | `just check` |
