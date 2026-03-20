#!/usr/bin/env bash
set -euo pipefail

PAPER_ID="${1:?paper id required}"
BASE="corpus/papers/${PAPER_ID}"

mkdir -p "${BASE}/source"
cat > "${BASE}/metadata.json" <<EOF
{
  "id": "${PAPER_ID}",
  "title": "",
  "authors": [],
  "year": 1900,
  "domain": "other",
  "source": {
    "kind": "pdf",
    "path": "${BASE}/source/source.pdf",
    "sha256": "REPLACE_WITH_REAL_HASH"
  },
  "artifact_status": "admitted"
}
EOF

echo "[]" > "${BASE}/claims.json"
echo "[]" > "${BASE}/assumptions.json"
echo "[]" > "${BASE}/symbols.json"
echo "{}" > "${BASE}/mapping.json"
echo "{}" > "${BASE}/manifest.json"

echo "Created ${BASE}"
