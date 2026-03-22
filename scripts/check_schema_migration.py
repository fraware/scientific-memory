#!/usr/bin/env python3
"""
CI gate: if any file under schemas/*.schema.json changed, docs/contributor-playbook.md must also have changed.
Usage: from repo root, run with optional --base REF (default: main). Compares --base..HEAD.
Exits 0 if check passes, 1 if schema files changed without a migration note doc change.
"""

import argparse
import subprocess
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Check schema changes have migration notes")
    parser.add_argument("--base", default="main", help="Base ref to compare (default: main)")
    parser.add_argument("--head", default="HEAD", help="Head ref (default: HEAD)")
    args = parser.parse_args()
    repo_root = Path(__file__).resolve().parents[1]
    if not (repo_root / ".git").exists():
        # Not a git repo (e.g. in a tarball); skip check
        return 0
    try:
        # Use merge base so we only see changes introduced in this branch (e.g. PR)
        base_ref = subprocess.run(
            ["git", "merge-base", args.base, args.head],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=True,
            timeout=5,
        )
        merge_base = base_ref.stdout.strip()
        if not merge_base:
            return 0
        out = subprocess.run(
            ["git", "diff", "--name-only", f"{merge_base}..{args.head}"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=True,
            timeout=10,
        )
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        return 0
    changed = [line.strip() for line in out.stdout.splitlines() if line.strip()]
    schema_changed = any(s.startswith("schemas/") and s.endswith(".schema.json") for s in changed)
    doc_changed = "docs/contributor-playbook.md" in changed
    if schema_changed and not doc_changed:
        print(
            "Schema files changed but docs/contributor-playbook.md was not updated. "
            "Add a migration note under Schema versioning and migration notes in that file.",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
