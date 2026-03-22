#!/usr/bin/env bash
# Run lake fmt when this Lake build supports it; otherwise exit 0 (no-op).
# Keeps local/CI workflows working across Lake versions that omit `lake fmt`.
set -euo pipefail
set +e
_out=$(lake fmt "$@" 2>&1)
_ec=$?
set -e
if [ "$_ec" -eq 0 ]; then
  if [ -n "$_out" ]; then
    printf '%s\n' "$_out"
  fi
  exit 0
fi
if printf '%s' "$_out" | grep -q 'unknown command'; then
  echo "note: lake fmt skipped (not available in this Lake build)" >&2
  exit 0
fi
printf '%s\n' "$_out" >&2
exit "$_ec"
