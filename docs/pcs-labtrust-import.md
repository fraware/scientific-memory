# PCS LabTrust import

Scientific Memory imports **signed** `ScienceClaimBundle` artifacts produced by the LabTrust v0.1 demonstration workflow and verified or signed by Provability Fabric.

## Expected input

- File: `signed_science_claim_bundle.json`
- Top-level `schema_version`: `SignedScienceClaimBundle.v0`
- Nested `science_claim_bundle` with `ScienceClaimBundle.v0`
- Optional top-level `verification_result` (`VerificationResult.v0`)
- Top-level `signature_or_digest`

Canonical artifact vocabulary is defined in [pcs-core](https://github.com/SentinelOps-CI/pcs-core). Scientific Memory does **not** own PCS schemas; it mirrors pcs-core under `schemas/pcs/` and calls `pcs_core` when installed:

| Canonical (pcs-core) | Legacy alias (deprecated) |
|----------------------|---------------------------|
| `SignedScienceClaimBundle.v0.schema.json` | `signed_science_claim_bundle.schema.json` |
| `ScienceClaimBundle.v0.schema.json` | `science_claim_bundle.schema.json` |
| `VerificationResult.v0.schema.json` | `verification_result.schema.json` |

Two bundle shapes are supported:

| Shape | Nested claim | Receipt / certificate |
|-------|----------------|----------------------|
| LabTrust portal (legacy) | `science_claim_bundle.claim` | singular `runtime_receipt`, `trace_certificate` |
| pcs-core / Provability Fabric | `science_claim_bundle.claim_artifact` | `runtime_receipts[]`, `certificates[]` |

## Commands

```bash
# just uses positional arguments (not make-style BUNDLE=path)
just pcs-validate-bundle path/to/signed_science_claim_bundle.json
just pcs-import-bundle path/to/signed_science_claim_bundle.json
just pcs-import-legacy-bundle path/to/legacy_signed_bundle.json
just pcs-render-claim <claim_id>

# shortcuts
just pcs-import-labtrust-demo
just pcs-refresh-demo
```

**Windows:** run `just` from Git Bash (configured in the justfile). For live pcs-core tests: `just test-pcs-integration`. Install pcs-core when cloned as a sibling repo: `just sync-pipeline-pcs`.

`pcs-import-bundle` writes:

- `corpus/pcs/claims/<claim_id>/signed_bundle.json` — preserved signed input
- `corpus/pcs/claims/<claim_id>/read_model.json` — portal read model
- `corpus/pcs/claims/<claim_id>/import_manifest.json` — warnings and provenance (legacy)
- `corpus/pcs/claims/<claim_id>/scientific_memory_import_report.json` — import report (`claim_id`, `imported_at`, `source_bundle_path`, `verification_status`, `warnings`, `stale_artifacts`, `render_path`)

`pcs-render-claim` refreshes `portal/.generated/pcs-export.json` for static portal build.

```bash
just sync-pcs-schemas       # copy canonical schemas from repo-root/pcs-core
just refresh-pcs-fixtures   # sync signed_science_claim_bundle.json + read model from pcs-core
just refresh-pcs-corpus     # import canonical + legacy demos into corpus/pcs/claims/
just pcs-refresh-demo       # fixtures + corpus + portal export
```

After Provability Fabric signs a bundle:

```bash
pf sign science-claim science_claim_bundle.certified.json --out signed_science_claim_bundle.json
uv run python scripts/refresh_pcs_canonical_fixture.py --signed path/to/signed_science_claim_bundle.json --copy-to-fixture --sync-pcs-core-alias
just refresh-pcs-corpus
```

Schema layout:

- `schemas/pcs/*.schema.json` — mirrors synced from pcs-core (canonical)
- `schemas/pcs/legacy/*.schema.json` — LabTrust portal legacy envelopes only
- `schemas/pcs/SCHEMA_MIRROR.json` — provenance manifest from last sync

Top-level `reproduce_commands` / `verify_commands` are Scientific Memory extensions; they are stripped before pcs-core validation and preserved in the stored signed bundle and read model.

## Import behavior

| Behavior | Detail |
|----------|--------|
| Validation | JSON Schema + optional `pcs_core` hook |
| Strict default | PCS Core signed bundles accepted; legacy LabTrust envelopes require `--allow-legacy` |
| Reject invalid (`strict=true`, default) | Missing `science_claim_bundle`, claim, assumption set, runtime receipt, certificate (signed bundles), failed or missing `verification_result`, empty assumptions, missing `source_commit` / `signature_or_digest` on major artifacts |
| `strict=false` | May import legacy bundles and bundles without `VerificationResult` (warning only) |
| Canonical fixture | `tests/pcs/fixtures/signed_science_claim_bundle.json` (from pcs-core / `pf sign science-claim …`) |
| Preserve IDs | Claim, assumption set, receipt, certificate IDs unchanged |
| Preserve provenance | `source_repo`, `source_commit`, `signature_or_digest` on each artifact |
| Preserve checks | Provability Fabric `VerificationResult.v0` `checks` stored verbatim |
| Reject: empty assumptions | `assumption_set.assumptions` must be non-empty |

### Provability Fabric handoff shape

```json
{
  "schema_version": "v0",
  "signed_bundle_id": "...",
  "science_claim_bundle": {},
  "verification_result": {},
  "signer": "Provability Fabric",
  "signed_at": "...",
  "signature_or_digest": "sha256:..."
}
```

## End-to-end LabTrust flow (reference)

```bash
# LabTrust-Gym
labtrust run-demo qc-release
labtrust export-trace --run runs/qc-release --out trace.json
labtrust export-runtime-receipt --run runs/qc-release --out runtime_receipt.json
labtrust export-pcs --run runs/qc-release --out science_claim_bundle.pending.json

# CertifyEdge
certifyedge emit-pcs-certificate \
  --spec templates/hospital_lab/qc_release.stl \
  --trace trace.json \
  --out trace_certificate.json

labtrust attach-certificate \
  --bundle science_claim_bundle.pending.json \
  --certificate trace_certificate.json \
  --out science_claim_bundle.certified.json

# Provability Fabric
pf verify science-claim science_claim_bundle.certified.json
pf sign science-claim science_claim_bundle.certified.json \
  --out signed_science_claim_bundle.json

# Scientific Memory
just pcs-import-bundle BUNDLE=signed_science_claim_bundle.json
just pcs-render-claim CLAIM_ID=<claim_id>
```

## What is checked vs not checked

**Checked (when present in bundle):**

- Schema shape for signed bundle, science claim bundle, and verification result
- Non-empty assumption set
- Artifact hash fields on nested artifacts (surfaced in portal hash table)
- Provability Fabric verification checks (listed under Verification Result)
- Runtime receipt and trace certificate status values (displayed, not re-verified)

**Not checked by Scientific Memory v0.1:**

- Live LabTrust simulation re-run
- CertifyEdge certificate re-generation
- Temporal trace re-validation against production hospital systems
- Clinical or production medical certification

See [pcs-rendering-contract.md](./pcs-rendering-contract.md) for portal section requirements.
