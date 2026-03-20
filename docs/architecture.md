# Architecture

Scientific Memory is a monorepo with these main areas:

- **corpus**: schema-first paper metadata, claims, assumptions, symbols; one directory per paper.
- **formal**: Lean 4 library (`ScientificMemory`) with mathlib; namespaces mirror domain slices.
- **schemas**: canonical JSON schemas for papers, claims, assumptions, theorem cards, manifests, and kernels.
- **pipeline**: Python (`uv`) ingestion, extraction, normalization, validation, and publish tooling (`sm_pipeline`), including a **gate engine** ([`validate/gate_engine.py`](../pipeline/src/sm_pipeline/validate/gate_engine.py)) that runs checks in a fixed order, optional **stage orchestration** ([`pipeline_orchestrator.py`](../pipeline/src/sm_pipeline/pipeline_orchestrator.py)) for SPEC 8.x-shaped workflows, and **portal read model** ([`publish/portal_read_model.py`](../pipeline/src/sm_pipeline/publish/portal_read_model.py)) for `corpus-export.json`. Extension hooks and publication entry points are documented in [pipeline-extension-points.md](pipeline-extension-points.md).
- **kernels**: executable kernels with declared verification boundaries; shared numeric test helpers live in the workspace package [`kernels/conformance/`](../kernels/conformance/) (`kernel-conformance`).
- **portal**: Next.js app rendering from canonical corpus/manifests/exported bundle.
- **benchmarks**: benchmark tasks and regression thresholds.

## Build and validation flow

Build stack:

- Lean/Lake for formal code
- Python/uv for pipeline
- pnpm/Next.js for portal

Validation (`just validate` / `sm_pipeline.cli validate-all`) runs the **gate engine**, which enforces, in order:

- JSON Schema checks (including theorem cards and kernels when present),
- normalization integrity (unique IDs, resolved links),
- provenance integrity (source spans + declaration mapping),
- graph integrity (theorem-card dependencies and kernel/card/manifest references),
- coverage integrity,
- extraction run requirement (papers with non-empty claims must have `extraction_run.json`),
- migration doc check when schemas change,
- reviewer lifecycle (invalid claim status rejected; disputed without `review_notes` rejected),
- snapshot baseline quality warnings (non-blocking).

Optional: `validate-all --report-json <path>` writes a machine-readable report after success.

## CI and release gates

Core workflows:

- **Corpus validation CI**: pipeline tests, kernel tests, validation (including extraction_run for papers with claims), benchmark regression (proof-success snapshot, runtime budgets, `tasks` minima and `tasks_ceiling` in `baseline_thresholds.json`).
- **Portal CI**: portal lint, build, manifest-driven route smoke test, non-empty dependency graph assertion for Langmuir.
- **Release workflow**: packages artifacts, emits checksums/changelog, runs deterministic checksum verification (`scripts/verify_release_checksums.sh`), then **Sigstore (cosign) keyless signing** of `dist/checksums.txt`, then creates a **GitHub Release** for the tag with uploaded assets (CHANGELOG, checksums, signatures, `release-bundle.zip`).

Gate 7: checksums plus Sigstore signing; optional signature verification in verify script when `.sig` and `.pem` are present; consumers may download the release bundle from GitHub Releases.

## Contributor diagnostics

- `just doctor` verifies `uv`, `pnpm`, `lean`, and `lake` availability.
- `just check` prints stage banners for fail-stage visibility.
- `just lake-build-verbose LOG=...` captures Lean build logs deterministically.

## Portal data model

The portal reads from canonical corpus files and can prefer the exported bundle `portal/.generated/corpus-export.json` produced by `just export-portal-data` (built by `sm_pipeline.publish.portal_read_model.build_portal_bundle`).

Static routes for papers, claims, theorem cards, and kernels are pre-rendered at build time.

Client Components in the portal (e.g. dependency graph views) must receive **serializable** props from Server Components only: for example, precomputed `nodeHrefById` maps instead of passing function callbacks across the server/client boundary.
