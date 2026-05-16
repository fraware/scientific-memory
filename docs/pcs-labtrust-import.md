# PCS LabTrust import

Scientific Memory imports **signed** `ScienceClaimBundle` artifacts produced by the LabTrust v0.1 demonstration workflow and verified or signed by Provability Fabric.

## Expected input

- File: `signed_science_claim_bundle.json`
- Top-level `schema_version`: `SignedScienceClaimBundle.v0`
- Nested `science_claim_bundle` with `ScienceClaimBundle.v0`
- Optional top-level `verification_result` (`VerificationResult.v0`)
- Top-level `signature_or_digest`

Canonical artifact vocabulary is defined in [pcs-core](https://github.com/SentinelOps-CI/pcs-core). This repository validates against vendored JSON Schemas under `schemas/pcs/` and calls `pcs_core` (editable path dependency in `pipeline/pyproject.toml`) for canonical `ScienceClaimBundle.v0` and `VerificationResult.v0` shapes.

Two bundle shapes are supported:

| Shape | Nested claim | Receipt / certificate |
|-------|----------------|----------------------|
| LabTrust portal (legacy) | `science_claim_bundle.claim` | singular `runtime_receipt`, `trace_certificate` |
| pcs-core / Provability Fabric | `science_claim_bundle.claim_artifact` | `runtime_receipts[]`, `certificates[]` |

## Commands

```bash
just pcs-validate-bundle BUNDLE=path/to/signed_science_claim_bundle.json
just pcs-import-bundle BUNDLE=path/to/signed_science_claim_bundle.json
just pcs-render-claim CLAIM_ID=<claim_id>
```

`pcs-import-bundle` writes:

- `corpus/pcs/claims/<claim_id>/signed_bundle.json` — preserved signed input
- `corpus/pcs/claims/<claim_id>/read_model.json` — portal read model
- `corpus/pcs/claims/<claim_id>/import_manifest.json` — warnings and provenance

`pcs-render-claim` refreshes `portal/.generated/pcs-export.json` for static portal build.

## Import behavior

| Behavior | Detail |
|----------|--------|
| Validation | JSON Schema + optional `pcs_core` hook |
| Reject invalid | Default (`strict=true`) |
| Preserve IDs | Claim, assumption set, receipt, certificate IDs unchanged |
| Preserve provenance | `source_repo`, `source_commit`, `signature_or_digest` on each artifact |
| Preserve checks | VerificationResult `checks` list stored verbatim |
| Warn: no VerificationResult | Import continues; portal shows advisory |
| Warn: certificate not checked | When `trace_certificate.status` ≠ `CertificateChecked` |
| Reject: empty assumptions | `assumption_set.assumptions` must be non-empty |

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
