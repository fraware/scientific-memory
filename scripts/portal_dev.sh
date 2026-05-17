#!/usr/bin/env bash
# Start portal dev server (single instance; avoids .next/trace EPERM on Windows).
set -euo pipefail
_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# shellcheck source=just_env.sh
source "$_root/scripts/just_env.sh"

bash "$_root/scripts/portal_install.sh"

export PORT="${PORT:-3000}"
if command -v netstat >/dev/null 2>&1; then
  if netstat -ano 2>/dev/null | grep -q ":${PORT} .*LISTENING"; then
    echo "portal: port $PORT is in use; stopping existing listeners..."
    bash "$_root/scripts/portal_stop.sh"
    sleep 1
  fi
fi

# Stale trace profile from experimental.cpus or a duplicate dev process.
rm -rf "$_root/portal/.next/trace" 2>/dev/null || true

cd "$_root/portal"
echo "portal: http://localhost:${PORT}"
echo "  PCS claims: http://localhost:${PORT}/pcs/claims/claim-pcs-qc-release-v0.1"
exec pnpm exec next dev -p "$PORT"
