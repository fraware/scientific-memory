#!/usr/bin/env bash
# Install portal workspace deps when needed (skip when Next.js is already present).
set -euo pipefail
_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# shellcheck source=just_env.sh
source "$_root/scripts/just_env.sh"

portal_next="$_root/portal/node_modules/.bin/next"
if [[ -x "$portal_next" ]] || [[ -f "$portal_next" ]] || [[ -f "$portal_next.cmd" ]]; then
  echo "portal: node_modules OK (next present), skipping pnpm install"
  exit 0
fi

echo "portal: installing workspace dependencies..."
if ! pnpm install --dir "$_root"; then
  if [[ -x "$portal_next" ]] || [[ -f "$portal_next" ]] || [[ -f "$portal_next.cmd" ]]; then
    echo "portal: pnpm install failed (often TLS); using existing next binary"
    exit 0
  fi
  echo "portal: pnpm install failed and next is missing. Fix npm TLS/proxy or run from a network that can reach registry.npmjs.org." >&2
  exit 1
fi
