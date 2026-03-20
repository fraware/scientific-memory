#!/usr/bin/env bash
set -euo pipefail

echo "Packaging release artifacts..."
mkdir -p dist
# Copy corpus and manifests for release bundle (required)
if [ ! -d "corpus" ]; then
  echo "ERROR: corpus/ missing; release bundle incomplete." >&2
  exit 1
fi
cp -r corpus dist/

# Changelog: from last tag to HEAD (Gate 7)
if git describe --tags --abbrev=0 2>/dev/null; then
  PREV_TAG=$(git describe --tags --abbrev=0 2>/dev/null)
  echo "## Changelog (${PREV_TAG}..HEAD)" > dist/CHANGELOG.md
  echo "" >> dist/CHANGELOG.md
  git log --oneline "${PREV_TAG}..HEAD" 2>/dev/null >> dist/CHANGELOG.md || true
else
  echo "## Changelog" > dist/CHANGELOG.md
  git log --oneline -20 >> dist/CHANGELOG.md 2>/dev/null || true
fi
if [ ! -s "dist/CHANGELOG.md" ]; then
  echo "ERROR: dist/CHANGELOG.md empty or missing." >&2
  exit 1
fi

# Manifest checksum: hash of all paper manifest.json (Gate 7)
: > dist/checksums.txt
if [ -d "dist/corpus/papers" ]; then
  MANIFEST_CHECKSUM=$(find dist/corpus/papers -name "manifest.json" -print0 | xargs -0 cat 2>/dev/null | sort | sha256sum | cut -d' ' -f1)
  echo "manifest_checksum=${MANIFEST_CHECKSUM}" >> dist/checksums.txt
fi

# Artifact hash: per-file checksums and overall digest (Gate 7)
if ! command -v sha256sum >/dev/null 2>&1; then
  echo "ERROR: sha256sum required for release integrity." >&2
  exit 1
fi
(cd dist && find . -type f | sort | xargs sha256sum) >> dist/checksums.txt
ARTIFACT_HASH=$(cd dist && find . -type f | sort | xargs cat | sha256sum | cut -d' ' -f1)
echo "release_artifact_sha256=${ARTIFACT_HASH}" >> dist/checksums.txt
echo "Release artifact SHA256: ${ARTIFACT_HASH}"

if [ ! -s "dist/checksums.txt" ]; then
  echo "ERROR: dist/checksums.txt empty or missing." >&2
  exit 1
fi
echo "Release artifacts in dist/ (CHANGELOG.md, checksums.txt)"

if command -v uv >/dev/null 2>&1; then
  uv run python scripts/release_corpus_delta.py 2>/dev/null || true
fi
