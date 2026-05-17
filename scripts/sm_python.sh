#!/usr/bin/env bash
# Run pipeline CLI with an interpreter that already has deps (avoids PyPI on every just recipe).
set -euo pipefail
_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# shellcheck source=just_env.sh
source "$_root/scripts/just_env.sh"

export PYTHONPATH="$_root/pipeline/src${PYTHONPATH:+:$PYTHONPATH}"

_python_candidates() {
  # Prefer active conda/system Python (has pipeline deps); root .venv often lacks sm-pipeline.
  command -v python 2>/dev/null || true
  command -v python3 2>/dev/null || true
  if [ -x "$_root/pipeline/.venv/Scripts/python.exe" ]; then
    echo "$_root/pipeline/.venv/Scripts/python.exe"
  fi
  if [ -x "$_root/pipeline/.venv/bin/python" ]; then
    echo "$_root/pipeline/.venv/bin/python"
  fi
  if [ -x "$_root/.venv/Scripts/python.exe" ]; then
    echo "$_root/.venv/Scripts/python.exe"
  fi
  if [ -x "$_root/.venv/bin/python" ]; then
    echo "$_root/.venv/bin/python"
  fi
}

if [ "${SM_FORCE_UV:-0}" != "1" ]; then
  while IFS= read -r py; do
    [ -n "$py" ] || continue
    if "$py" -c "import typer" 2>/dev/null; then
      exec "$py" "$@"
    fi
  done < <(_python_candidates)
fi

if uv run --help 2>/dev/null | grep -q -- '--no-sync'; then
  exec uv run --no-sync --native-tls --project "$_root/pipeline" python "$@"
fi

exec uv run --native-tls --project "$_root/pipeline" python "$@"
