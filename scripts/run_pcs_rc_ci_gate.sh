#!/usr/bin/env bash
# PCS RC + Phase 2 gate: drift, strict import/render, contract tests.
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

echo "==> PCS: ensure Phase 2 fixtures"
python "$_root/scripts/ensure_labtrust_phase2_fixtures.py"

echo "==> PCS RC: fixture drift (signed bundle vs pcs-core)"
python "$_root/scripts/sync_labtrust_release_from_pcs_core.py" --no-corpus
git diff --exit-code tests/pcs/fixtures/labtrust-release/signed_science_claim_bundle.json || {
  echo "error: SM signed bundle drifted from pcs-core; run: just refresh-pcs-release" >&2
  exit 1
}

_pcs_labtrust="${PCS_CORE_PATH:-}/examples/labtrust-release"
_pcs_manifest=""
for _name in release_manifest.v0.json ReleaseManifest.v0.json; do
  if [ -f "$_pcs_labtrust/$_name" ]; then
    _pcs_manifest="$_pcs_labtrust/$_name"
    break
  fi
done
if [ -n "$_pcs_manifest" ]; then
  echo "==> PCS RC: ReleaseManifest artifact hash parity (signed bundle entry)"
  python - "$_pcs_manifest" <<'PY'
import json
import sys
from pathlib import Path

repo = Path(".")
sm = json.loads((repo / "tests/pcs/fixtures/labtrust-release/ReleaseManifest.v0.json").read_text())
pcs = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8-sig"))
key = "signed_science_claim_bundle.json"
if sm["artifacts"][key]["sha256"] != pcs["artifacts"][key]["sha256"]:
    print("ReleaseManifest signed bundle hash mismatch vs pcs-core labtrust release", file=sys.stderr)
    raise SystemExit(1)
print("OK: ReleaseManifest signed bundle hash matches pcs-core labtrust release")
PY
fi

echo "==> PCS: pytest (full tests/pcs suite)"
python -m pytest "$_root/tests/pcs" -q

if command -v just >/dev/null 2>&1; then
  echo "==> PCS: just pcs-import-release (Phase 2 primary path)"
  just -f "$_root/JUSTFILE" pcs-import-release
  echo "==> PCS: just pcs-render-claim"
  just -f "$_root/JUSTFILE" pcs-render-claim claim-pcs-qc-release-v0.1
else
  echo "==> PCS: CLI import-release (just not installed)"
  python -m sm_pipeline.cli pcs-import-release \
    --release-manifest tests/pcs/fixtures/labtrust-release/ReleaseManifest.v0.json
  python -m sm_pipeline.cli pcs-render-claim --claim-id claim-pcs-qc-release-v0.1
fi

echo "==> PCS: import report Phase 2 fields"
python - <<'PY'
import json
import sys
from pathlib import Path

report = Path("corpus/pcs/claims/claim-pcs-qc-release-v0.1/scientific_memory_import_report.json")
data = json.loads(report.read_text(encoding="utf-8"))
required = (
    "release_chain_validation_id",
    "release_chain_validation_status",
    "release_chain_validator",
    "release_chain_checked_at",
    "release_manifest_hash",
)
missing = [k for k in required if k not in data]
if missing:
    print("missing import report keys:", ", ".join(missing), file=sys.stderr)
    sys.exit(1)
if data.get("release_chain_validation_status") != "ProofChecked":
    print("expected ProofChecked release chain status", file=sys.stderr)
    sys.exit(1)
print("OK: import report Phase 2 fields present")
PY

echo "==> PCS: portal read-model contracts"
_portal="$_root/portal"
if [ ! -d "$_portal/node_modules/zod" ]; then
  echo "error: portal node_modules missing; run: cd portal && npm install" >&2
  exit 1
fi
if command -v pnpm >/dev/null 2>&1; then
  pnpm --dir "$_portal" test:pcs-contract
  pnpm --dir "$_portal" test:pcs-phase2-contract
  pnpm --dir "$_portal" test:pcs-tool-use-phase2-contract
else
  node "$_portal/scripts/verify-pcs-read-model.mjs"
  node "$_portal/scripts/verify-pcs-phase2-read-model.mjs" \
    "$_root/corpus/pcs/claims/claim-pcs-qc-release-v0.1/read_model.json"
  node "$_portal/scripts/verify-pcs-phase2-read-model.mjs" \
    "$_root/tests/pcs/fixtures/tool-use-release/.phase2-read-model.json"
fi

echo "OK: PCS RC + Phase 2 gate passed"
