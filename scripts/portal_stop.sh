#!/usr/bin/env bash
# Stop Next.js dev servers bound to portal ports (Windows + Unix).
set -euo pipefail
_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

_stop_port() {
  local port="$1"
  if command -v netstat >/dev/null 2>&1 && command -v taskkill >/dev/null 2>&1; then
    local pids
    pids="$(netstat -ano 2>/dev/null | grep ":${port} " | grep LISTENING | awk '{print $NF}' | sort -u || true)"
    for pid in $pids; do
      [[ -z "$pid" || "$pid" == "0" ]] && continue
      echo "portal-stop: killing PID $pid on port $port"
      taskkill //F //PID "$pid" 2>/dev/null || true
    done
    return 0
  fi
  if command -v lsof >/dev/null 2>&1; then
    local pids
    pids="$(lsof -ti :"$port" 2>/dev/null || true)"
    for pid in $pids; do
      echo "portal-stop: killing PID $pid on port $port"
      kill "$pid" 2>/dev/null || true
    done
  fi
}

for port in 3000 3001; do
  _stop_port "$port"
done

# Release .next trace locks left by a crashed or duplicate dev server.
rm -rf "$_root/portal/.next/trace" 2>/dev/null || true
echo "portal-stop: done"
