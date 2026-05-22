#!/usr/bin/env bash
# Release-grade Scientific Memory PCS benchmark producer gate (pcs-bench consumable ingest).
set -euo pipefail
_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# shellcheck source=just_env.sh
source "$_root/scripts/just_env.sh"

export PYTHONPATH="$_root/pipeline/src${PYTHONPATH:+:$PYTHONPATH}"

PCS_CORE="${PCS_CORE_PATH:-}"
if [ -z "$PCS_CORE" ]; then
  if [ -d "$_root/pcs-core/schemas" ]; then
    PCS_CORE="$_root/pcs-core"
  elif [ -d "$_root/../pcs-core/schemas" ]; then
    PCS_CORE="$(cd "$_root/../pcs-core" && pwd)"
  fi
fi
if [ -z "$PCS_CORE" ] || [ ! -d "$PCS_CORE/schemas" ]; then
  echo "error: pcs-core checkout required (set PCS_CORE_PATH or clone sibling pcs-core)" >&2
  exit 1
fi

CASES="${PCS_BENCH_CASES:-benchmarks/rendering/labtrust_qc_release}"
OUT="${PCS_BENCH_OUT:-benchmark_runs/labtrust_rendering}"
INGEST="$OUT/pcs_bench_ingest.v0.json"

echo "==> PCS producer: release-grade rendering benchmark ($CASES)"
python -m sm_pipeline.cli pcs-benchmark-rendering \
  --cases "$_root/$CASES" \
  --out "$_root/$OUT" \
  --validate-pcs-core-output "$PCS_CORE" \
  --release-grade

echo "==> PCS producer: validate ingest (SM + pcs-core)"
python "$_root/scripts/validate_pcs_bench_ingest.py" \
  --input "$_root/$INGEST" \
  --pcs-core "$PCS_CORE" \
  --release-grade

if command -v pcs-bench >/dev/null 2>&1; then
  echo "==> PCS producer: pcs-bench validate-ingest"
  pcs-bench validate-ingest --input "$_root/$INGEST" --pcs-core "$PCS_CORE"
else
  echo "warn: pcs-bench CLI not on PATH; skipped external validate-ingest" >&2
fi

echo "OK: PCS benchmark producer gate passed -> $INGEST"
