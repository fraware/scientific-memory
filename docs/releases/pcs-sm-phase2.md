# pcs-sm Phase 2 — release protocol consumer

Scientific Memory consumes PCS Phase 2 protocol artifacts defined in **pcs-core** (no local schema variants). Phase 2 makes the LabTrust RC chain importable and reviewable as a single release unit.

## Protocol artifacts (pcs-core canonical)

| Artifact | Role in Scientific Memory |
|----------|---------------------------|
| `ReleaseManifest.v0` | Entry point for release import; artifact registry metadata |
| `ReleaseChainValidationResult.v0` | Required proof that the chain passed (`ProofChecked`) |
| `HandoffManifest.v0` | Schema mirrored; produced upstream between repos |
| SignedScienceClaimBundle.v0 | Imported claim payload (unchanged from v0.1) |

Registry rows are derived from `ReleaseManifest.v0` artifact entries plus chain validation checks until `ArtifactRegistry.v0` ships in pcs-core.

## Import (primary)

```bash
just pcs-import-release
```

Requires in the same directory:

- `ReleaseManifest.v0.json`
- `ReleaseChainValidationResult.v0.json`
- All artifacts listed in the manifest (including `signed_science_claim_bundle.json`)

Equivalent:

```bash
just pcs-import-release-manifest tests/pcs/fixtures/labtrust-release/ReleaseManifest.v0.json
```

## Import report (Phase 2 fields)

After import, `scientific_memory_import_report.json` includes:

- `release_id`, `release_candidate`, `release_manifest_hash`, `validation_profile`
- `release_chain_validation_id`
- `release_chain_validation_status` (`ProofChecked`)
- `release_chain_validator`
- `release_chain_checked_at`

## Corpus layout

```text
corpus/pcs/claims/<claim_id>/
  signed_bundle.json
  read_model.json
  release_manifest.json
  release_chain_validation.json
  lineage.json
  scientific_memory_import_report.json
```

## Portal sections

`read_model.json` and `/pcs/claims/<id>` render:

- Claim, Assumptions, Runtime Evidence, Temporal Certificate, Verification Result
- **Release Manifest**, **Release Chain Validation**, **Artifact Registry**, Artifact Dependency Graph
- Artifact Hashes, Source Repositories, Reproduce / Verify, Limitations

## Claim queries

```bash
just pcs-list-claims
just pcs-show-claim claim-pcs-qc-release-v0.1
just pcs-check-stale claim-pcs-qc-release-v0.1
just pcs-list-claims-by-certificate cert-trace-886c95f0-5d63-42d6-aa13-5891c12c5a6a
just pcs-list-claims-by-source-commit 5b4b81049b430d1b59ff5b51f688eb0feaeef76c
```

## Stale tracking

`lineage.json` records certificate ID, trace hash, signed bundle hash, release manifest hash, and producer commits. `pcs-check-stale` compares on-disk artifacts to lineage and sets `stale` / `stale_reasons`.

## CI gate

```bash
just pcs-rc-gate
```

Runs full `tests/pcs`, `pcs-import-release`, render, import-report Phase 2 assertions, and portal contracts (`test:pcs-contract`, `test:pcs-phase2-contract`).

## Refresh fixtures

```bash
just refresh-pcs-release
```

Syncs from `pcs-core/examples/labtrust-release/`, ensures Phase 2 manifests (`scripts/ensure_labtrust_phase2_fixtures.py`), and re-validates the chain.
