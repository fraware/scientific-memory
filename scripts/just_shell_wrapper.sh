#!/usr/bin/env bash
# Invoked as: bash scripts/just_shell_wrapper.sh -cu "<recipe body>"
# Sources PATH fixes then delegates to bash with the same arguments.
set -euo pipefail
_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# shellcheck source=just_env.sh
source "$_root/scripts/just_env.sh"
exec bash "$@"
