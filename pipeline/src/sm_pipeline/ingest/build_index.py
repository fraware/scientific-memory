"""Build `corpus/index.json` from paper metadata files."""

from __future__ import annotations

import json
from pathlib import Path


def build_index(repo_root: Path) -> Path:
    """
    Rebuild corpus index from canonical paper metadata.

    The output shape intentionally stays compact because this index is
    consumed by portal listing pages and CLI tooling.
    """
    repo_root = repo_root.resolve()
    papers_dir = repo_root / "corpus" / "papers"
    papers: list[dict[str, object]] = []
    if papers_dir.is_dir():
        for paper_dir in sorted(papers_dir.iterdir()):
            if not paper_dir.is_dir():
                continue
            metadata_path = paper_dir / "metadata.json"
            if not metadata_path.exists():
                continue
            try:
                metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                continue
            if not isinstance(metadata, dict) or not metadata.get("id"):
                continue
            papers.append(
                {
                    "id": str(metadata.get("id")),
                    "title": str(metadata.get("title") or ""),
                    "year": int(metadata.get("year") or 0),
                    "domain": str(metadata.get("domain") or "other"),
                }
            )

    out = {"version": "0.1", "papers": papers}
    out_path = repo_root / "corpus" / "index.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, indent=2), encoding="utf-8")
    return out_path
