#!/usr/bin/env bash
# PCS v0.1 RC gate: drift check, strict CLI import/render, contract tests.
set -euo pipefail
_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# shellcheck source=just_env.sh
source "$_root/scripts/just_env.sh"

export PYTHONPATH="$_root/pipeline/src${PYTHONPATH:+:$PYTHONPATH}"
if [ -d "$_root/pcs-core/examples/labtrust-release" ]; then
  export PCS_CORE_PATH="$_root/pcs-core"
elif [ -d "$_root/../pcs-core/examples/labtrust-release" ]; then
  export PCS_CORE_PATH="$_root/../pcs-core"
fi

echo "==> PCS RC: fixture drift (signed bundle vs pcs-core)"
python "$_root/scripts/sync_labtrust_release_from_pcs_core.py" --no-corpus
git diff --exit-code tests/pcs/fixtures/labtrust-release/signed_science_claim_bundle.json || {
  echo "error: SM signed bundle drifted from pcs-core; run: just refresh-pcs-release" >&2
  exit 1
}

echo "==> PCS RC: pytest gate"
python -m pytest \
  "$_root/tests/pcs/test_canonical_rc.py" \
  "$_root/tests/pcs/test_pcs_release_negatives.py" \
  -q

if command -v just >/dev/null 2>&1; then
  echo "==> PCS RC: just pcs-import-rc-bundle"
  just -f "$_root/JUSTFILE" pcs-import-rc-bundle
  echo "==> PCS RC: just pcs-render-claim"
  just -f "$_root/JUSTFILE" pcs-render-claim claim-pcs-qc-release-v0.1
else
  echo "==> PCS RC: CLI import (just not installed)"
  python -m sm_pipeline.cli pcs-import-bundle \
    --bundle tests/pcs/fixtures/labtrust-release/signed_science_claim_bundle.json \
    --strict --release-mode
  python -m sm_pipeline.cli pcs-render-claim --claim-id claim-pcs-qc-release-v0.1
fi

echo "==> PCS RC: portal read-model contract"
pnpm --dir "$_root/portal" test:pcs-contract

echo "OK: PCS RC gate passed"
