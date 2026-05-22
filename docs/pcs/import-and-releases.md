# Import and releases

Scientific Memory consumes PCS artifacts from pcs-core. The **recommended** path is a full release directory with `ReleaseManifest.v0.json` and a passing `ReleaseChainValidationResult.v0.json`. A **signed bundle only** path remains for older workflows.

## Release import (recommended)

```bash
just pcs-import-release
```

Default manifest: `tests/pcs/fixtures/labtrust-release/ReleaseManifest.v0.json`.

Refresh fixtures from pcs-core first:

```bash
just sync-labtrust-release
just pcs-import-release
```

Custom manifest:

```bash
just pcs-import-release RELEASE_MANIFEST=path/to/ReleaseManifest.v0.json
```

### Required release artifacts

| Artifact | Role |
|----------|------|
| `ReleaseManifest.v0` | Primary import entry; lists all release files |
| `ReleaseChainValidationResult.v0` | Proof the chain passed (`ProofChecked`) |
| `SignedScienceClaimBundle.v0` | Claim payload |
| `ArtifactRegistry.v0` | Optional registry metadata |
| `HandoffManifest.v0` | Producer handoff chain |
| `WorkflowProfile.v0` | Resolved from `workflow_profile_id` on chain validation |

Strict release mode sets `strict=true`, `allow_legacy=false`, and keeps import reports free of fixture field overlays.

Python module (equivalent):

```bash
python -m sm_pipeline.pcs_import.release_manifest_importer \
  --manifest tests/pcs/fixtures/labtrust-release/ReleaseManifest.v0.json \
  --release-mode \
  --render
```

### Tool-use safety release

```bash
just sync-tool-use-release
just pcs-import-tool-use-release
```

Fixture: `tests/pcs/fixtures/tool-use-release/`.

### Computation reproducibility release

```bash
just sync-computation-release
just bootstrap-computation-release   # regenerate fixtures when needed
just verify-computation-release
just pcs-import-computation-release
just pcs-import-computation-rejected-release   # rejected witness (failure evidence)
```

Fixtures:

- `tests/pcs/fixtures/computation-release/` — passed witness
- `tests/pcs/fixtures/computation-rejected-release/` — rejected witness
- Published copy: `examples/computation-release/`

Workflow: `scientific_computation.reproducibility_v0`.

## Signed bundle import (legacy)

For a single `signed_science_claim_bundle.json` without a release manifest:

```bash
just pcs-validate-bundle path/to/signed_science_claim_bundle.json
just pcs-import-bundle path/to/signed_science_claim_bundle.json --strict --release-mode
just pcs-render-claim <claim_id>
```

Shortcuts:

```bash
just pcs-import-labtrust-release
just pcs-import-rc-bundle    # vendored LabTrust fixture, strict mode
```

### Bundle shapes

| Shape | Claim field | Receipt / certificate |
|-------|-------------|------------------------|
| pcs-core / Provability Fabric | `claim_artifact` | `runtime_receipts[]`, `certificates[]` |
| LabTrust portal (legacy) | `claim` | singular `runtime_receipt`, `trace_certificate` |

Legacy envelopes require `--allow-legacy` on `pcs-import-bundle`.

### Expected signed bundle

- `schema_version`: `SignedScienceClaimBundle.v0`
- Nested `science_claim_bundle` with `ScienceClaimBundle.v0`
- Optional `verification_result` (`VerificationResult.v0`)
- Top-level `signature_or_digest`

Canonical fixture `tests/pcs/fixtures/labtrust-release/signed_science_claim_bundle.json` is synced from pcs-core and should be refreshed via `refresh-pcs-release` instead of isolated edits.

### Import outputs

Each import writes under `corpus/pcs/claims/<claim_id>/`:

- `signed_bundle.json` — preserved input
- `read_model.json` — portal read model
- `scientific_memory_import_report.json` — status, warnings, release chain fields

`pcs-render-claim` refreshes `portal/.generated/pcs-export.json`.

### Strict mode rejects

- Legacy bundles without `--allow-legacy`
- Missing or failed `verification_result`
- Placeholder `source_commit` values
- Certificate or trace hash mismatches
- Missing signatures or provenance on major artifacts

### Limitation notice

Every claim includes a mandatory limitation in `read_model.limitation_notice` and the portal. The text states that the artifact is proof-carrying simulation evidence, not clinical or production medical certification.

## Refresh fixtures from pcs-core

Atomic sync (schemas + all release trains + Phase 2 fixtures):

```bash
just refresh-pcs-release
# Windows / without bash:
python scripts/refresh_pcs_release.py
```

Refresh committed corpus and portal export for all release trains:

```bash
just refresh-pcs-corpus-all
```

Individual syncs:

```bash
just sync-pcs-schemas
just sync-labtrust-release
just sync-tool-use-release
just sync-computation-release
```

Legacy alias: `just refresh-pcs-fixtures` (same as `refresh-pcs-release`).

The release gate re-syncs from pcs-core and fails if the signed bundle still differs from the last committed fixture. Commit fixture updates after a successful refresh.

## Query commands

Commands read `corpus/pcs/claims_index.json` and per-claim `lineage.json`.

```bash
just pcs-list-claims
just pcs-show-claim claim_id=claim-pcs-qc-release-v0.1
just pcs-check-stale claim_id=claim-pcs-qc-release-v0.1
just pcs-refresh-stale
just pcs-list-stale-claims
just pcs-list-claims-by-certificate certificate_id=...
just pcs-list-claims-by-source-commit COMMIT=...
just pcs-list-claims-by-release release_id=...
just pcs-list-claims-by-workflow workflow_id=...
just pcs-query-lineage
just pcs-query-lineage --stale-only
```

Formal trust and computation filters are documented in the [portal rendering guide](portal-rendering.md).

## Compare releases

```bash
just pcs-compare-releases release-pcs-v0.1-labtrust-qc release-pcs-v0.2-example
```

Both `release_id` values must exist in `claims_index.json` from prior imports.

## Formal trust (Lean-checked obligations)

When the workflow profile requires formal trust, import includes `ProofObligation.v0` and `LeanCheckResult.v0`:

```bash
just bootstrap-formal-trust-release
just pcs-import-release
just pcs-show-formal-checks CLAIM_ID=claim-pcs-qc-release-v0.1
```

Cross-repo flow (pcs-core → Provability Fabric → Scientific Memory) is in pcs-core and Provability Fabric documentation; Scientific Memory imports the resulting release directory.

## Staleness

Claim states: `current`, `stale`, `superseded`, `withdrawn`, `revalidated`.

Triggers include signed bundle hash drift, release manifest hash change, certificate or trace hash change, source commit change, schema version change, and failed revalidation.

## End-to-end reference (LabTrust demo)

```bash
# LabTrust-Gym — generate trace and bundle
labtrust run-demo qc-release
labtrust export-trace --run runs/qc-release --out trace.json
labtrust export-runtime-receipt --run runs/qc-release --out runtime_receipt.json
labtrust export-pcs --run runs/qc-release --out science_claim_bundle.pending.json

# CertifyEdge — temporal certificate
certifyedge emit-pcs-certificate \
  --spec templates/hospital_lab/qc_release.stl \
  --trace trace.json \
  --out trace_certificate.json

labtrust attach-certificate \
  --bundle science_claim_bundle.pending.json \
  --certificate trace_certificate.json \
  --out science_claim_bundle.certified.json

# Provability Fabric — verify and sign
pf verify science-claim science_claim_bundle.certified.json
pf sign science-claim science_claim_bundle.certified.json \
  --out signed_science_claim_bundle.json

# Scientific Memory — import and render
just pcs-import-bundle ../LabTrust-Gym/signed_science_claim_bundle.json --strict --release-mode
just pcs-render-claim claim-pcs-qc-release-v0.1
```

## What Scientific Memory checks

**Checked when present:** JSON Schema shape, non-empty assumptions, artifact hashes, verification checks, runtime and certificate status display.

**Not checked:** Live LabTrust re-run, CertifyEdge re-generation, production hospital validation, clinical certification.

## Schema mirrors

Scientific Memory mirrors pcs-core schemas under `schemas/pcs/`. Sync with:

```bash
just sync-pcs-schemas
```

Legacy aliases live under `schemas/pcs/legacy/` for old LabTrust portal envelopes only.

## Tests

```bash
just test-pcs
```

Contract tests: `tests/pcs/test_pcs_import.py`, `tests/pcs/test_pcs_render.py`, portal scripts `verify-pcs-read-model.mjs` and `verify-pcs-phase2-read-model.mjs`.
