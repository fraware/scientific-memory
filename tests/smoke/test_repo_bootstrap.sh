#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$REPO_ROOT"
# shellcheck source=../../scripts/just_env.sh
source "$REPO_ROOT/scripts/just_env.sh"

if ! command -v uv >/dev/null 2>&1; then
  echo "Smoke: uv not found; install uv or add its Scripts/.local/bin to PATH" >&2
  exit 127
fi

echo "Smoke: validate-all"
uv run --project pipeline python -m sm_pipeline.cli validate-all

echo "Smoke: pipeline tests"
uv run python -m pytest pipeline/tests -q

echo "Smoke: kernel tests"
uv run python -m pytest kernels/adsorption/tests -q

echo "Smoke: repo bootstrap passed"
