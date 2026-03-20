"""Validate snapshot baseline quality: title, narrative, highlights for release baselines."""

import json
from pathlib import Path


def validate_snapshot_quality(repo_root: Path) -> list[str]:
    """
    Check corpus/snapshots/*.json for release baseline quality.
    Returns list of warning messages (non-blocking).
    """
    repo_root = repo_root.resolve()
    snapshots_dir = repo_root / "corpus" / "snapshots"
    if not snapshots_dir.is_dir():
        return []

    warnings: list[str] = []
    for path in sorted(snapshots_dir.glob("*.json")):
        if path.name == "README.md":  # skip if any
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        if not isinstance(data, dict):
            continue

        title = str(data.get("title") or "").strip()
        narrative = str(data.get("narrative") or "").strip()
        highlights = data.get("highlights")
        if not isinstance(highlights, list):
            highlights = []

        # Require non-empty title and narrative (min 10 chars)
        if not title:
            warnings.append(f"{path.name}: missing or empty 'title'")
        if len(narrative) < 10:
            warnings.append(f"{path.name}: 'narrative' too short (min 10 chars)")

        # For release-tagged baselines, require at least one highlight
        is_release = (
            path.name.startswith("release-")
            or path.name.startswith("v")
            or path.name == "last-release.json"
        )
        if is_release and len(highlights) == 0:
            warnings.append(
                f"{path.name}: release baseline should have non-empty 'highlights' array"
            )

    return warnings
