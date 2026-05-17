# pcs-sm-v0.1.0-rc1

Scientific Memory is the human-facing evidence layer for Proof-Carrying Science (PCS) release candidate `pcs-v0.1.0-rc1`. It imports the canonical signed bundle from `pcs-core/examples/labtrust-release/`, validates strict release mode, persists corpus artifacts, builds a portal read model, and renders the verified claim for review.

## Trust loop (this repo’s role)

```text
LabTrust-Gym trace
  → RuntimeReceipt.v0
  → CertifyEdge TraceCertificate.v0
  → ScienceClaimBundle.v0
  → Provability Fabric VerificationResult.v0
  → SignedScienceClaimBundle.v0
  → Scientific Memory import and rendering   ← this repository
```

Canonical fixtures are vendored from [pcs-core `examples/labtrust-release/`](https://github.com/SentinelOps-CI/pcs-core/tree/main/examples/labtrust-release). Do not regenerate partial fixtures independently; run `just refresh-pcs-release` to sync the full atomic chain.

## RC-pinned values

| Field | Value |
|--------|--------|
| Claim ID | `claim-pcs-qc-release-v0.1` |
| Certificate ID | `cert-trace-886c95f0-5d63-42d6-aa13-5891c12c5a6a` |
| Trace hash | `sha256:c3e8a3dc4ad86d533de1dfa4ae7fe2a338c2cff3c945404c96a75216524d58cd` |
| Scientific Memory commit | `5b4b81049b430d1b59ff5b51f688eb0feaeef76c` |

## Import the signed bundle (strict release mode)

```bash
just pcs-import-rc-bundle
```

Equivalent:

```bash
just pcs-import-bundle \
  tests/pcs/fixtures/labtrust-release/signed_science_claim_bundle.json \
  --strict --release-mode
```

`--release-mode` enforces strict PCS Core import, rejects legacy shapes, and pins `scientific_memory_import_report.json` fields from the fixture beside the bundle.

### Import report (expected)

- `verification_status`: `passed`
- `strict`: `true`
- `allow_legacy`: `false`
- `bundle_shape`: `pcs_core`
- `scientific_memory_commit`: `5b4b81049b430d1b59ff5b51f688eb0feaeef76c`

## Where artifacts are stored

After import, corpus layout:

```text
corpus/pcs/claims/claim-pcs-qc-release-v0.1/
  signed_bundle.json
  read_model.json
  import_manifest.json
  scientific_memory_import_report.json
```

Test fixtures (synced from pcs-core):

```text
tests/pcs/fixtures/labtrust-release/
release-run/                    # atomic promotion staging directory
```

## Read model contents

`read_model.json` is normalized from the signed bundle for portal rendering. It includes:

- **Claim** — claim artifact, guarantee types, signature/digest
- **Assumptions** — assumption set and entries
- **Runtime Evidence** — runtime receipt (trace hash, policy hash, events)
- **Temporal Certificate** — trace certificate ID and digest
- **Verification Result** — Provability Fabric checks and status
- **Artifact Hashes** — per-artifact digests and canonical digest map
- **Source Repositories** — `source_repo` / `source_commit` provenance
- **Reproduce / Verify** — `reproduce_commands` and `verify_commands`
- **Limitations** — mandatory limitation notice (see below)

Golden read model: `tests/pcs/fixtures/canonical_pcs_read_model.json`.

## Render the claim

```bash
just pcs-render-claim claim-pcs-qc-release-v0.1
```

Writes `portal/.generated/pcs-export.json` for the Next.js PCS portal (`/pcs/claims/claim-pcs-qc-release-v0.1`).

## Strict mode rejects

Strict release import (`--strict --release-mode`) rejects:

- Legacy LabTrust portal bundle shapes (without `--allow-legacy`)
- Missing or failed `verification_result`
- Placeholder or local-dev `source_commit` values
- Tampered certificate IDs (mismatch with verification `certificate_refs`)
- Tampered runtime receipt `trace_hash` (mismatch with certificate trace hash)
- Missing signatures or provenance on PCS Core artifacts

## Limitations notice (mandatory)

Every imported claim must carry this notice in `read_model.limitation_notice` and the portal UI:

> This artifact is a proof-carrying simulation result. It demonstrates protocol-level and runtime-evidence verification inside LabTrust-Gym. It is not a clinical validation, production medical certification, or guarantee about a real hospital laboratory.

## Phase 2 release import

Prefer `just pcs-import-release` when `ReleaseManifest.v0.json` and `ReleaseChainValidationResult.v0.json` are present. See [pcs-sm-phase2.md](./pcs-sm-phase2.md).

## CI and drift protection

```bash
just pcs-rc-gate
```

Runs:

1. Phase 2 fixture validation and signed-bundle byte parity vs `pcs-core`
2. Full `tests/pcs` suite (69+ tests)
3. `just pcs-import-release` and `just pcs-render-claim claim-pcs-qc-release-v0.1`
4. Portal v0.1 and Phase 2 read-model zod contracts

CI fails if `tests/pcs/fixtures/labtrust-release/signed_science_claim_bundle.json` drifts from `pcs-core`.

## Refresh after pcs-core RC updates

```bash
just refresh-pcs-release
```

Then verify `RELEASE_FIXTURE_MANIFEST.json` `scientific_memory_commit` matches the RC git tag and re-run `just pcs-rc-gate`.
