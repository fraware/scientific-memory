"""Portable paths for scientific_memory_import_report.json (reproducible across OS)."""

from __future__ import annotations

from pathlib import Path


def portable_repo_path(path: Path, repo_root: Path) -> str:
    """Prefer a repo-relative POSIX path; fall back to filename."""
    try:
        return path.resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError:
        return path.name
