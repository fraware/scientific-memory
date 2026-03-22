# End-to-end scenarios: trust hardening and LLM sidecars

Manual or scripted checks that mirror the comprehensive test plan. Automated coverage lives under `pipeline/tests/test_trust_hardening_*.py`, `test_llm_proposals.py`, `test_llm_lean_proposals.py`, and `test_benchmark_runner.py`.

## Scenario A: Scaffold-only extraction with empty claims

1. Create a paper with `metadata.json` and no `claims.json` (or `claims.json` as `[]`).
2. Run extract-claims with `--mode scaffold_only` (or default).
3. Expect a non-empty `claims.json` with the placeholder claim, `extraction_run.json` containing `extraction_mode` and `placeholder_claim_written: true`.

## Scenario B: Deterministic mode without scaffolding

1. Same paper layout as A but run extract-claims with `--mode deterministic` (or `llm_sidecar`) and no pre-existing claims file.
2. Expect no placeholder claim: after normalization, `claims.json` is an empty array `[]`, and `placeholder_claim_written` is false in `extraction_run.json`.

## Scenario C: Unresolved links after normalization

1. In `claims.json`, set `linked_assumptions` / `linked_symbols` to mix valid IDs and unknown IDs (or use `_unresolved` fields).
2. Run `normalize-paper` (or extract-claims, which runs normalize).
3. Expect valid IDs on `linked_assumptions` / `linked_symbols`, unknown IDs on `linked_assumptions_unresolved` / `linked_symbols_unresolved`, and matching fields in `normalization_report.json`.

## Scenario D: Suggestion sidecars (warn-only)

1. Add an invalid `llm_claim_proposals.json`, `llm_lean_proposals.json`, or `suggested_assumptions.json` under a paper directory.
2. Run `validate-all` or the gate runner.
3. Expect stderr warnings for suggestion sidecars; pipeline must not fail solely on invalid optional sidecars.

## Scenario F: LLM Lean assist (suggest-only, human-gated apply)

1. Run `llm-lean-proposals` with `--use-fake-provider` or a live model; expect `llm_lean_proposals.json` only (no `formal/` writes).
2. Review JSON; run `llm-lean-proposals-to-apply-bundle` for one `proposal_id` with non-empty `replacements`.
3. Run `proof-repair-apply` without `--apply`, then only apply on a branch after human sign-off. See [llm-lean-live-test-matrix.md](llm-lean-live-test-matrix.md).

## Scenario E: Publish recomputes manifest graphs

1. Edit `manifest.json` to set a fake `dependency_graph` and `kernel_index` that do not match the corpus.
2. Run `publish-artifacts` for that paper without `SM_PUBLISH_REUSE_MANIFEST_GRAPHS`.
3. Expect `dependency_graph` and `kernel_index` recomputed from current theorem cards and `corpus/kernels.json`.
4. Repeat publish twice with no source edits; expect stable `build_hash` and `build_hash_version` `2` (see `test_double_publish_identical_build_hash`).
5. With `SM_PUBLISH_REUSE_MANIFEST_GRAPHS=1`, expect prior manifest graph fields to be retained when still present.

## Related commands

- `uv run --project pipeline ruff check pipeline/src/sm_pipeline`
- `uv run --project pipeline python -m sm_pipeline.cli validate-all`
- `uv run --project pipeline pytest pipeline/tests -q`
- `uv run --project pipeline python -m sm_pipeline.cli benchmark`
- `uv run python scripts/generate_repo_snapshot.py`

See [trust-boundary-and-extraction.md](../reference/trust-boundary-and-extraction.md) and [ADR 0012](../adr/0012-trust-boundary-canonical-artifacts.md).
