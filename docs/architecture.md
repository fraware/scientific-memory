# Architecture

Scientific Memory is a monorepo with these main areas:

- **corpus**: schema-first paper metadata, claims, assumptions, symbols; one directory per paper.
- **formal**: Lean 4 library (`ScientificMemory`) with mathlib; namespaces mirror domain slices.
- **schemas**: canonical JSON schemas for papers, claims, assumptions, theorem cards, manifests, and kernels.
- **pipeline**: Python (`uv`) ingestion, extraction, normalization, validation, and publish tooling (`sm_pipeline`), including a **gate engine** ([`validate/gate_engine.py`](../pipeline/src/sm_pipeline/validate/gate_engine.py)) that runs checks in a fixed order, optional **stage orchestration** ([`pipeline_orchestrator.py`](../pipeline/src/sm_pipeline/pipeline_orchestrator.py)) for SPEC 8.x-shaped workflows, and **portal read model** ([`publish/portal_read_model.py`](../pipeline/src/sm_pipeline/publish/portal_read_model.py)) for `corpus-export.json`. Extension hooks and publication entry points are documented in [pipeline-extension-points.md](pipeline-extension-points.md).
- **kernels**: executable kernels with declared verification boundaries; shared numeric test helpers live in the workspace package [`kernels/conformance/`](../kernels/conformance/) (`kernel-conformance`).
- **portal**: Next.js app rendering from canonical corpus/manifests/exported bundle, including proof-carrying claim pages under `/pcs/claims/` and assurance action pages under `/assurance`.
- **benchmarks**: benchmark tasks and regression thresholds, including PCS rendering suites and the Gate 6 `assurance` task.
- **corpus/pcs**: imported proof-carrying releases (signed bundles, release manifests, read models). See [pcs/README.md](pcs/README.md).
- **corpus/assurance**: append-only scientific action chains, outcomes, and calibrations. See [assurance/README.md](assurance/README.md) and [ADR 0014](adr/0014-assurance-action-chain.md).

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
- reviewer lifecycle (invalid claim status rejected; disputed claims require non-empty `review_notes`),
- PCS corpus integrity (`pcs_corpus`),
- assurance corpus integrity (`assurance_corpus`: schema registry, digests, action-chain DAGs under `corpus/assurance/`),
- snapshot baseline quality warnings (non-blocking).

Optional: `validate-all --report-json <path>` writes a machine-readable report after success.

### Non-blocking warnings

After strict checks succeed, `validate-all` may still print stderr warnings while keeping exit code zero—snapshot baseline quality (for example `corpus/snapshots/last-release.json` metadata), **dependency graph bootstrap** hints when a paper has multiple theorem cards and empty `dependency_ids` alongside machine-checked claims (tier-0 Lean regex extraction may leave an empty graph), and **suggestion sidecar** schema issues for optional `llm_*_proposals.json` (including `llm_lean_proposals.json`) and `suggested_*.json` under paper directories. See [trust-boundary-and-extraction.md](reference/trust-boundary-and-extraction.md).

### Manifest fingerprint and graphs

`publish_manifest` sets `manifest.build_hash_version` to **2** where `claims.json` exists (content-addressed digest over canonical corpus JSON, theorem cards, kernel index, and optional metadata source SHA256). Each publish recomputes `dependency_graph` and `kernel_index` from current cards and `corpus/kernels.json` unless `SM_PUBLISH_REUSE_MANIFEST_GRAPHS=1` is set.

Provenance checks remain strict for normal papers. Hard-dimension intake scaffolds tagged `hardness.primary:*` with empty `claims.json` may use the all-zero `metadata.source.sha256` sentinel during intake only.

## CI and release

Core workflows:

- **Corpus validation CI**: pipeline tests, kernel tests, validation (including extraction_run for papers with claims), benchmark regression (proof-success snapshot, runtime budgets, `tasks` minima and `tasks_ceiling` in `baseline_thresholds.json`).
- **Portal CI**: portal lint, build, manifest-driven route smoke test, non-empty dependency graph assertion for Langmuir.
- **Release workflow**: packages artifacts, emits checksums/changelog, runs deterministic checksum verification (`scripts/verify_release_checksums.sh`), then **Sigstore (cosign) keyless signing** of `dist/checksums.txt`, then creates a **GitHub Release** for the tag with uploaded assets (CHANGELOG, checksums, signatures, `release-bundle.zip`).

Release integrity combines checksums with Sigstore signing, and verifiers may confirm signatures when `.sig` and `.pem` are present. See [Release integrity](contributor-playbook.md#release-integrity-gate-7).

PCS workflows (`corpus-validation`, `pcs-bench-producer`) run release verification and producer gates when pcs-core and pcs-bench are available. Operator documentation lives in [pcs/README.md](pcs/README.md).

Assurance corpus validation runs inside `just validate` / `validate-all` as gate `assurance_corpus`. Portal assurance pages consume only `portal/.generated/assurance-export.json` (`just export-assurance-portal-data`). The layer is not a live authorization or execution system; see [assurance/README.md](assurance/README.md).

## Contributor diagnostics

- `just doctor` verifies `uv`, `pnpm`, `lean`, and `lake` availability.
- `just check` prints stage banners for fail-stage visibility.
- `just lake-build-verbose LOG=...` captures Lean build logs deterministically.

## Portal data model

The portal reads from canonical corpus files and can prefer the exported bundle `portal/.generated/corpus-export.json` produced by `just export-portal-data` (built by `sm_pipeline.publish.portal_read_model.build_portal_bundle`). PCS claim pages use `portal/.generated/pcs-export.json`; assurance action pages use `portal/.generated/assurance-export.json`.

The export bundle now includes precomputed lookup indices under `indices` (claim, theorem-card, declaration, and kernel reverse lookups). Portal read paths should use these indices first, then fall back to direct corpus scans only when no export is available.

Current bundle contract is version `0.3` (`PORTAL_BUNDLE_VERSION`) and includes route-oriented theorem-card ids (`indices.all_theorem_card_route_ids`) plus claim and kernel lookup maps used by `portal/lib/data.ts`.

Static routes for papers, claims, theorem cards, and kernels are pre-rendered at build time.

Client Components in the portal (for example dependency graph views) must receive **serializable** props from Server Components only—for example precomputed `nodeHrefById` maps that replace function callbacks across the server/client boundary.
