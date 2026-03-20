#!/usr/bin/env bash
# Verify Gate 7 release checksums (deterministic recomputation check).
set -euo pipefail

if [ ! -f "dist/checksums.txt" ]; then
  echo "ERROR: dist/checksums.txt missing; cannot verify." >&2
  exit 1
fi
if [ ! -f "dist/CHANGELOG.md" ]; then
  echo "ERROR: dist/CHANGELOG.md missing." >&2
  exit 1
fi

# Recompute manifest_checksum from dist/corpus/papers
if [ -d "dist/corpus/papers" ]; then
  RECOMPUTED=$(find dist/corpus/papers -name "manifest.json" -print0 | xargs -0 cat 2>/dev/null | sort | sha256sum | cut -d' ' -f1)
  RECORDED=$(grep '^manifest_checksum=' dist/checksums.txt | cut -d= -f2-)
  if [ -z "$RECORDED" ]; then
    echo "ERROR: manifest_checksum not found in dist/checksums.txt" >&2
    exit 1
  fi
  if [ "$RECOMPUTED" != "$RECORDED" ]; then
    echo "ERROR: manifest_checksum mismatch (recomputed=$RECOMPUTED, recorded=$RECORDED)" >&2
    exit 1
  fi
  echo "Verified manifest_checksum"
fi

# Ensure release_artifact_sha256 is present
if ! grep -q '^release_artifact_sha256=' dist/checksums.txt; then
  echo "ERROR: release_artifact_sha256 missing in dist/checksums.txt" >&2
  exit 1
fi
echo "Release checksum verification passed."

# Optional: verify Sigstore signature when present (Gate 7 signing)
if [ -f "dist/checksums.txt.sig" ] && [ -f "dist/checksums.txt.pem" ] && command -v cosign >/dev/null 2>&1; then
  if cosign verify-blob dist/checksums.txt --signature=dist/checksums.txt.sig --certificate=dist/checksums.txt.pem; then
    echo "Sigstore signature verification passed."
  else
    echo "ERROR: Sigstore signature verification failed." >&2
    exit 1
  fi
fi
