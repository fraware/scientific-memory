# pcs-sm Phase 2 — release evidence interface

Scientific Memory is the **human-facing evidence layer** for PCS releases: it imports `ReleaseManifest.v0`, requires `ReleaseChainValidationResult.v0`, renders protocol metadata, tracks lineage, and exposes cross-claim queries.

## Protocol artifacts (pcs-core canonical)

| Artifact | Role in Scientific Memory |
|----------|---------------------------|
| `ReleaseManifest.v0` | Primary import entry; artifact registry metadata |
| `ReleaseChainValidationResult.v0` | Required proof that the chain passed (`ProofChecked`) |
| `artifact_registry.valid.json` | Vendored from pcs-core; enriches registry rows |
| `HandoffManifest.v0` | Schema mirrored; produced upstream between repos |
| `SignedScienceClaimBundle.v0` | Claim payload |

## Import (primary)

```bash
just pcs-import-release
# or
just pcs-import-release RELEASE_MANIFEST=tests/pcs/fixtures/labtrust-release/ReleaseManifest.v0.json
```

Requires in the same directory:

- `ReleaseManifest.v0.json`
- `ReleaseChainValidationResult.v0.json`
- All artifacts listed in the manifest (including `signed_science_claim_bundle.json`)

Python module entry:

```bash
python -m sm_pipeline.pcs_import.release_manifest_importer \
  --manifest tests/pcs/fixtures/labtrust-release/ReleaseManifest.v0.json
```

Release imports **never** overlay `scientific_memory_import_report.json` from sibling fixtures. Bundle-only `--release-mode` on fixture paths may still overlay for legacy RC tests.

## Import report (protocol-computed)

`scientific_memory_import_report.json` includes:

- `release_id`, `release_candidate`, `release_manifest_hash`, `validation_profile`
- `release_chain_validation_id`, `release_chain_validation_status`, `release_chain_validator`, `release_chain_checked_at`
- `signed_bundle_hash`, `certificate_id`, `trace_hash`, `artifact_registry_version`

## Corpus layout

```text
corpus/pcs/
  claims_index.json          # cross-claim lineage index
  claims/<claim_id>/
    signed_bundle.json
    read_model.json
    release_manifest.json
    release_chain_validation.json
    lineage.json
    scientific_memory_import_report.json
```

## Portal sections

`/pcs/claims/<id>` renders:

- Claim, Assumptions, Runtime Evidence, Temporal Certificate, Verification Result
- Release Manifest, Release Chain Validation, Artifact Registry, Artifact Dependency Graph
- **Lineage**, **Staleness**
- Artifact Hashes, Source Repositories, Reproduce / Verify, Limitations

`/pcs` lists claims with release ID and fresh/stale badges.

## Cross-claim queries

```bash
just pcs-list-claims
just pcs-show-claim claim-pcs-qc-release-v0.1
just pcs-check-stale claim-pcs-qc-release-v0.1
just pcs-refresh-stale                    # recompute all stale flags + index
just pcs-list-stale-claims
just pcs-list-claims-by-certificate CERTIFICATE_ID=cert-trace-...
just pcs-list-claims-by-source-commit COMMIT=...
just pcs-list-claims-by-release RELEASE_ID=release-pcs-v0.1-labtrust-qc
just pcs-list-claims-by-trace-hash TRACE_HASH=sha256:...
just pcs-query-lineage                    # full claims_index.json
just pcs-query-lineage --stale-only
```

## CI gate

```bash
just pcs-rc-gate          # Linux / Git Bash
just pcs-rc-gate-py       # cross-platform Python gate
```

Runs `tests/pcs`, `pcs-import-release`, import-report assertions, portal contracts, and `claims_index.json` presence.

## Refresh fixtures

```bash
just refresh-pcs-release
```

Syncs from `pcs-core/examples/labtrust-release/`, ensures Phase 2 manifests, copies `artifact_registry.valid.json` into `schemas/pcs/`.
