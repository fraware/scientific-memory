# ADR 0010: Release integrity via checksums

## Status

Accepted.

## Context

SPEC Gate 7 requires "Manifest signed; changelog generated; release artifact hash emitted." The project needs a clear, maintainable way to satisfy release integrity without introducing heavy tooling in v0.1.

## Decision

Release integrity is implemented with **checksum-based integrity** plus **Sigstore (cosign) keyless signing**:

- The release workflow generates a changelog and writes `dist/checksums.txt` with a manifest checksum (over all paper manifest.json), per-file hashes, and a single release artifact SHA-256.
- "Manifest signed" is satisfied by (1) integrity and tamper detection via these checksums; (2) **Sigstore keyless signing** of `dist/checksums.txt` in the release workflow (signature and certificate written to `dist/checksums.txt.sig` and `dist/checksums.txt.pem`). No key management; GitHub OIDC attests origin.
- Verifiers can recompute hashes and optionally run `cosign verify-blob` when the `.sig` and `.pem` files are present. See [Contributor playbook – Release integrity (Gate 7)](../contributor-playbook.md#release-integrity-gate-7).

## Consequences

- Gate 7 is satisfied with checksums and optional cryptographic attestation (Sigstore).
- Verifiers can check integrity by recomputing hashes and optionally verifying the cosign signature.
