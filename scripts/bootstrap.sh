#!/usr/bin/env bash
set -euo pipefail

echo "==> installing python deps"
uv sync --all-packages

echo "==> installing node deps"
pnpm install

echo "==> updating Lake deps"
lake update

echo "==> bootstrap complete"
