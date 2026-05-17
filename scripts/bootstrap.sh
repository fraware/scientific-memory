#!/usr/bin/env bash
set -euo pipefail

echo "==> installing python deps"
uv sync --all-packages
if [ -d "../pcs-core/python" ] || [ -d "../../pcs-core/python" ] || [ -d "pcs-core/python" ]; then
  echo "==> installing pcs-core extra (pipeline)"
  uv sync --project pipeline --extra pcs || true
fi

echo "==> installing node deps"
pnpm install

echo "==> updating Lake deps"
lake update

echo "==> bootstrap complete"
