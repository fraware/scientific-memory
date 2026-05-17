#!/usr/bin/env bash
# PCS integration tests: live pcs-core validation (PCS_INTEGRATION=1 disables test mocks).
set -euo pipefail
_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# shellcheck source=just_env.sh
source "$_root/scripts/just_env.sh"

export PCS_INTEGRATION=1
export PYTHONPATH="$_root/pipeline/src${PYTHONPATH:+:$PYTHONPATH}"

for py in python python3; do
  if command -v "$py" >/dev/null 2>&1 && "$py" -c "import pytest" 2>/dev/null; then
    exec "$py" -m pytest "$_root/tests/pcs/test_pcs_integration.py" -v "$@"
  fi
done

exec uv run --no-sync --native-tls pytest "$_root/tests/pcs/test_pcs_integration.py" -v "$@"
