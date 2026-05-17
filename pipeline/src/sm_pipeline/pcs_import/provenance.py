"""Repository provenance helpers for PCS import reports."""

from __future__ import annotations

import subprocess
from pathlib import Path


def git_head_commit(repo_root: Path) -> str | None:
    """Return 40-hex HEAD for repo_root, or None when git is unavailable."""
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=repo_root,
            text=True,
            stderr=subprocess.DEVNULL,
        )
    except (subprocess.CalledProcessError, FileNotFoundError, OSError):
        return None
    commit = out.strip()
    return commit if len(commit) == 40 else None
