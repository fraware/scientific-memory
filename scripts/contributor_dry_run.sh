#!/usr/bin/env bash
# Contributor dry-run (SPEC Milestone 5): clone-friendly smoke path.
# Cross-OS clean-room: see docs/maintainers.md#clean-room-dry-run-maintainer
# Usage from a fresh clone:
#   ./scripts/contributor_dry_run.sh
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
command -v just >/dev/null 2>&1 || { echo "Install just (https://just.systems)"; exit 1; }
echo "== Doctor =="
just doctor || true
echo "== Validate =="
just validate
echo "== Tests =="
just test
echo "== Build =="
just build
echo "Dry-run OK: toolchain, validate, test, build."
