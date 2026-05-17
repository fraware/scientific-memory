"""Release-mode placeholder provenance detection (aligned with pcs-core release_fixtures)."""

from __future__ import annotations

import re

PLACEHOLDER_COMMIT_RE = re.compile(r"^(?:a{40}|b{40}|c{40}|d{40}|e{40}|0{40})$")

# Literal markers rejected for release / strict import (not valid git SHAs).
LOCAL_DEV_MARKERS = frozenset({"local-dev", "local_dev", "localdev"})


def is_placeholder_commit(commit: str) -> bool:
    """True when commit is a release placeholder pattern (aaaaaaaa…, cccc…, zeros, etc.)."""
    return bool(PLACEHOLDER_COMMIT_RE.fullmatch(str(commit or "").strip()))


def is_local_dev_marker(value: object) -> bool:
    if value is True:
        return True
    if isinstance(value, str) and value.strip().lower() in LOCAL_DEV_MARKERS:
        return True
    return False


def validate_source_commit_for_release(
    commit: str,
    *,
    path: str,
    local_dev: object = False,
) -> str | None:
    """Return an error message when commit is not acceptable for strict release import."""
    raw = str(commit or "").strip()
    if not raw:
        return f"{path}: source_commit is required"
    if is_local_dev_marker(local_dev):
        return f"{path}: local_dev is not allowed for release import"
    if is_local_dev_marker(raw):
        return f"{path}: source_commit must not be a local-dev marker"
    if is_placeholder_commit(raw):
        return f"{path}: source_commit must not be a placeholder commit"
    if len(raw) != 40 or not all(c in "0123456789abcdef" for c in raw.lower()):
        return f"{path}: source_commit must be a 40-character git commit hash"
    return None
