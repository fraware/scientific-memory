"""Claim extraction: ensure claims, assumptions, and symbols files exist and are valid."""

import json
from pathlib import Path

from sm_pipeline.extract.assumptions import extract_assumptions
from sm_pipeline.extract.normalize import normalize_paper
from sm_pipeline.extract.symbols import extract_symbols
from sm_pipeline.extract.report import write_extraction_run


def extract_claims(repo_root: Path, paper_id: str) -> None:
    """
    Ensure paper has valid claims.json, assumptions.json, symbols.json.
    If any are missing or empty, write minimal valid templates so the contributor can fill.
    """
    repo_root = repo_root.resolve()
    paper_dir = repo_root / "corpus" / "papers" / paper_id
    if not paper_dir.is_dir():
        raise FileNotFoundError(f"Paper directory not found: {paper_dir}")

    metadata_path = paper_dir / "metadata.json"
    if not metadata_path.exists():
        raise FileNotFoundError(
            f"Paper metadata not found: {metadata_path}. Run 'just add-paper {paper_id}' first."
        )
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    paper_id_val = metadata.get("id", paper_id)
    source_path = metadata.get("source", {}).get("path", "source/source.pdf")

    claims_path = paper_dir / "claims.json"
    if not claims_path.exists() or _empty_json_array(claims_path):
        claims = _template_claims(paper_id_val, source_path)
        claims_path.write_text(json.dumps(claims, indent=2), encoding="utf-8")

    extract_assumptions(repo_root, paper_id)
    extract_symbols(repo_root, paper_id)
    normalize_paper(repo_root, paper_id)

    try:
        write_extraction_run(repo_root, paper_id)
    except OSError:
        pass  # optional artifact; do not fail extraction


def _empty_json_array(path: Path) -> bool:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return isinstance(data, list) and len(data) == 0
    except (json.JSONDecodeError, OSError):
        return True


def _template_claims(paper_id: str, source_file: str) -> list[dict]:
    """One placeholder claim with valid source_span for contributor to replace."""
    claim_id = f"{paper_id.replace('-', '_')}_claim_001"
    return [
        {
            "id": claim_id,
            "paper_id": paper_id,
            "section": "1",
            "source_span": {
                "source_file": source_file,
                "start": {"page": 1, "offset": 0},
                "end": {"page": 1, "offset": 0},
            },
            "informal_text": "TODO: extract claim from source",
            "claim_type": "editorial_exposition",
            "status": "unparsed",
            "linked_symbols": [],
            "linked_assumptions": [],
            "linked_formal_targets": [],
        }
    ]
