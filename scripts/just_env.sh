#!/usr/bin/env bash
# Shared PATH bootstrap for non-interactive bash (just recipes, smoke tests).
# Git Bash on Windows usually inherits a full PATH; WSL/bash may not (uv only).
_winroot=""
for r in /c /mnt/c; do
  if [ -d "$r/Windows" ]; then
    _winroot="$r"
    break
  fi
done

# uv: common Windows install locations when env vars are missing in child shells.
if ! command -v uv >/dev/null 2>&1; then
  for p in \
    "${HOME:-}/.local/bin" \
    "${HOME:-}/.cargo/bin" \
    "${LOCALAPPDATA:-}/Programs/Python/Python313/Scripts" \
    "${LOCALAPPDATA:-}/Programs/Python/Python312/Scripts" \
    "${LOCALAPPDATA:-}/Programs/Python/Python311/Scripts"; do
    if [ -n "${p:-}" ] && [ -d "$p" ]; then
      export PATH="$p:$PATH"
      if command -v uv >/dev/null 2>&1; then
        break
      fi
    fi
  done
fi
if ! command -v uv >/dev/null 2>&1 && [ -n "${_winroot:-}" ]; then
  for p in \
    "${_winroot}/Users/${USER:-}/AppData/Local/Programs/Python/Python312/Scripts" \
    "${_winroot}/Users/${USERNAME:-}/AppData/Local/Programs/Python/Python312/Scripts" \
    "${_winroot}/Users/${USER:-}/AppData/Local/Programs/Python/Python313/Scripts" \
    "${_winroot}/Users/${USERNAME:-}/AppData/Local/Programs/Python/Python313/Scripts"; do
    if [ -n "${p:-}" ] && [ -d "$p" ]; then
      export PATH="$p:$PATH"
      if command -v uv >/dev/null 2>&1; then
        break
      fi
    fi
  done
fi

# Node: some shells only expose node.exe; pnpm scripts invoke `node`.
_repo="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
if ! command -v node >/dev/null 2>&1 && [ -n "${_winroot:-}" ]; then
  for p in \
    "${_winroot}/nvm4w/nodejs" \
    "${_winroot}/Program Files/nodejs" \
    "${HOME:-}/.local/bin" \
    "${_winroot}/Users/${USER:-}/AppData/Local/nvm" \
    "${_winroot}/Users/${USERNAME:-}/AppData/Local/nvm"; do
    if [ -n "${p:-}" ] && [ -d "$p" ]; then
      export PATH="$p:$PATH"
      if command -v node >/dev/null 2>&1; then
        break
      fi
    fi
  done
fi
if ! command -v node >/dev/null 2>&1 && command -v node.exe >/dev/null 2>&1; then
  export PATH="$_repo/scripts/node_bin:$PATH"
fi
