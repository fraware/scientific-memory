#!/usr/bin/env bash
# PCS contract tests from repo root (Windows-safe; avoids uv --project relative paths).
set -euo pipefail
_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# shellcheck source=just_env.sh
source "$_root/scripts/just_env.sh"

export PYTHONPATH="$_root/pipeline/src${PYTHONPATH:+:$PYTHONPATH}"
_tests="$_root/tests/pcs"

for py in python python3; do
  if command -v "$py" >/dev/null 2>&1 && "$py" -c "import pytest" 2>/dev/null; then
    exec "$py" -m pytest "$_tests" "$@"
  fi
done

exec uv run --no-sync --native-tls pytest "$_tests" "$@"
