"""Enforce extraction run artifacts when a paper has claims (SPEC 8.2)."""

from __future__ import annotations

import json
from pathlib import Path


class ExtractionArtifactError(Exception):
    """Raised when a paper with claims is missing extraction_run.json."""


def validate_extraction_run_required(repo_root: Path) -> None:
    """
    Require extraction_run.json for every paper that has non-empty claims.json.
    Raises ExtractionArtifactError if any such paper lacks the file.
    """
    repo_root = repo_root.resolve()
    papers_dir = repo_root / "corpus" / "papers"
    if not papers_dir.is_dir():
        return
    for paper_dir in sorted(papers_dir.iterdir()):
        if not paper_dir.is_dir():
            continue
        claims_path = paper_dir / "claims.json"
        if not claims_path.exists():
            continue
        try:
            claims = json.loads(claims_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        if not isinstance(claims, list) or len(claims) == 0:
            continue
        run_path = paper_dir / "extraction_run.json"
        if not run_path.exists():
            raise ExtractionArtifactError(
                f"Paper {paper_dir.name} has {len(claims)} claim(s) but no extraction_run.json. "
                "Run: sm-pipeline extraction-report --paper-id " + paper_dir.name
            )
