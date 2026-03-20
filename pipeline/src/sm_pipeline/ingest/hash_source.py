"""Hash paper source files and persist metadata.source.sha256."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


def hash_source_for_paper(repo_root: Path, paper_id: str) -> str:
    """
    Compute and persist source SHA-256 for one paper.

    Returns the computed hash; if the source file is missing, returns and writes
    the all-zero sentinel hash so schemas remain valid while intake continues.
    """
    repo_root = repo_root.resolve()
    metadata_path = repo_root / "corpus" / "papers" / paper_id / "metadata.json"
    if not metadata_path.exists():
        raise FileNotFoundError(f"Paper metadata not found: {metadata_path}")

    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    if not isinstance(metadata, dict):
        raise ValueError(f"Invalid metadata JSON object for paper {paper_id}")

    source = metadata.get("source") or {}
    if not isinstance(source, dict):
        source = {}
    source_path_raw = str(source.get("path") or "")
    source_path = (repo_root / source_path_raw).resolve() if source_path_raw else None

    if source_path and source_path.exists() and source_path.is_file():
        digest = _sha256_file(source_path)
    else:
        # Sentinel for "source not yet hashed"; papers with a manifest fail provenance until real source is hashed
        digest = "0" * 64

    source["sha256"] = digest
    metadata["source"] = source
    metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    return digest


def hash_all_sources(repo_root: Path) -> dict[str, str]:
    """Hash and persist source digests for all papers that have metadata files."""
    repo_root = repo_root.resolve()
    papers_dir = repo_root / "corpus" / "papers"
    result: dict[str, str] = {}
    if not papers_dir.is_dir():
        return result
    for paper_dir in sorted(papers_dir.iterdir()):
        if not paper_dir.is_dir():
            continue
        paper_id = paper_dir.name
        metadata_path = paper_dir / "metadata.json"
        if not metadata_path.exists():
            continue
        result[paper_id] = hash_source_for_paper(repo_root, paper_id)
    return result


def _sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        while True:
            chunk = fh.read(chunk_size)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()
