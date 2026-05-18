"""Resolve Phase 2 release artifact paths (pcs-core naming variants)."""

from __future__ import annotations

from pathlib import Path

RELEASE_MANIFEST_CANDIDATES = (
    "ReleaseManifest.v0.json",
    "release_manifest.v0.json",
)
RELEASE_CHAIN_VALIDATION_CANDIDATES = (
    "ReleaseChainValidationResult.v0.json",
    "release_chain_validation_result.v0.json",
)


def _first_existing(base: Path, names: tuple[str, ...]) -> Path | None:
    for name in names:
        candidate = base / name
        if candidate.is_file():
            return candidate
    return None


def resolve_release_manifest_path(release_dir: Path) -> Path:
    base = release_dir.resolve()
    found = _first_existing(base, RELEASE_MANIFEST_CANDIDATES)
    if found is not None:
        return found
    return base / RELEASE_MANIFEST_CANDIDATES[0]


def resolve_release_chain_validation_path(release_dir: Path) -> Path:
    base = release_dir.resolve()
    found = _first_existing(base, RELEASE_CHAIN_VALIDATION_CANDIDATES)
    if found is not None:
        return found
    return base / RELEASE_CHAIN_VALIDATION_CANDIDATES[0]
