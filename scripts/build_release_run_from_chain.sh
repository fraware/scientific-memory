#!/usr/bin/env bash
# Populate release-run/ from sibling LabTrust-Gym chain workdir.
set -euo pipefail
_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
exec bash "$_root/scripts/sm_python.sh" "$_root/scripts/build_release_run_from_chain.py" "$@"
