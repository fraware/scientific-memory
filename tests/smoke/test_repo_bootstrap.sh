#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$REPO_ROOT"

echo "Smoke: validate-all"
uv run --project pipeline python -m sm_pipeline.cli validate-all

echo "Smoke: pipeline tests"
uv run python -m pytest pipeline/tests -q

echo "Smoke: kernel tests"
uv run python -m pytest kernels/adsorption/tests -q

echo "Smoke: repo bootstrap passed"
