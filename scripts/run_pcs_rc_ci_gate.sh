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
if [ -f "$_root/tests/pcs/fixtures/labtrust-release/ReleaseManifest.v0.json" ]; then
  echo "==> PCS RC: ReleaseManifest artifact hash parity (signed bundle on disk)"
  python <<'PY'
import json
import sys
from pathlib import Path

repo = Path(".")
sys.path.insert(0, str(repo / "pipeline" / "src"))
from sm_pipeline.pcs_validate.canonical_hash import file_sha256_digest

sm = json.loads(
    (repo / "tests/pcs/fixtures/labtrust-release/ReleaseManifest.v0.json").read_text(
        encoding="utf-8-sig",
    ),
)
bundle = repo / "tests/pcs/fixtures/labtrust-release/signed_science_claim_bundle.json"
key = "signed_science_claim_bundle.json"
on_disk = file_sha256_digest(bundle)
if sm["artifacts"][key]["sha256"] != on_disk:
    print("ReleaseManifest signed bundle hash mismatch vs on-disk fixture", file=sys.stderr)
    raise SystemExit(1)
print("OK: ReleaseManifest signed bundle hash matches on-disk fixture")
PY
fi

if command -v just >/dev/null 2>&1; then
  echo "==> PCS: just pcs-import-release (Phase 2 primary path)"
  just -f "$_root/JUSTFILE" pcs-import-release
else
  echo "==> PCS: CLI import-release (just not installed)"
  python -m sm_pipeline.cli pcs-import-release \
    --release-manifest tests/pcs/fixtures/labtrust-release/ReleaseManifest.v0.json
fi

if [ -f "$_root/tests/pcs/fixtures/computation-release/release_manifest.v0.json" ]; then
  echo "==> PCS: computation-release fixture verify + import"
  python "$_root/scripts/verify_computation_release_fixture.py"
  python -m sm_pipeline.cli pcs-import-release \
    --release-manifest tests/pcs/fixtures/computation-release/release_manifest.v0.json
fi

python "$_root/scripts/verify_tool_use_release_fixture.py"

echo "==> PCS: pytest (full tests/pcs suite)"
python -m pytest "$_root/tests/pcs" -q

echo "==> PCS: release-grade producer gate (external reviewer, pcs-bench ingest)"
if [ -n "${PCS_CORE_PATH:-}" ] && [ -d "${PCS_CORE_PATH}/schemas" ]; then
  _gate_args=(--require-pcs-bench-cli)
  if [ ! -d "$_root/pcs-bench" ] && ! command -v pcs-bench >/dev/null 2>&1; then
    _gate_args=(--skip-pcs-bench-cli)
  fi
  python "$_root/scripts/run_pcs_bench_producer_gate.py" \
    --cases benchmarks/rendering/external_reviewer_minimal \
    --out benchmark_runs/pcs_rc_ci_rendering \
    --pcs-core "${PCS_CORE_PATH}" \
    "${_gate_args[@]}"
else
  echo "warn: PCS_CORE_PATH missing; skipping release-grade producer gate" >&2
fi

if command -v just >/dev/null 2>&1; then
  echo "==> PCS: just pcs-render-claim"
  just -f "$_root/JUSTFILE" pcs-render-claim claim-pcs-qc-release-v0.1
else
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
  pnpm --dir "$_portal" test:pcs-computation-phase2-contract
  pnpm --dir "$_portal" test:pcs-computation-rejected-phase2-contract
else
  node "$_portal/scripts/verify-pcs-read-model.mjs"
  node "$_portal/scripts/verify-pcs-phase2-read-model.mjs" \
    "$_root/corpus/pcs/claims/claim-pcs-qc-release-v0.1/read_model.json"
  node "$_portal/scripts/verify-pcs-phase2-read-model.mjs" \
    "$_root/tests/pcs/fixtures/tool-use-release/.phase2-read-model.json"
  node "$_portal/scripts/verify-pcs-phase2-read-model.mjs" \
    "$_root/tests/pcs/fixtures/computation-release/.phase2-read-model.json"
  node "$_portal/scripts/verify-pcs-phase2-read-model.mjs" \
    "$_root/tests/pcs/fixtures/computation-rejected-release/.phase2-read-model.json"
fi

echo "OK: PCS RC + Phase 2 gate passed"
