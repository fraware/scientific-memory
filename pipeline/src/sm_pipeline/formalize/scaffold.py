"""Scaffold formal mapping and optional Lean stubs from claims."""

import json
from pathlib import Path


def scaffold_formal(repo_root: Path, paper_id: str) -> None:
    """
    Ensure mapping.json exists and is valid for the paper.
    Sets paper_id, namespace, and claim_to_decl (preserving any existing entries).
    """
    repo_root = repo_root.resolve()
    paper_dir = repo_root / "corpus" / "papers" / paper_id
    if not paper_dir.is_dir():
        raise FileNotFoundError(f"Paper directory not found: {paper_dir}")

    metadata_path = paper_dir / "metadata.json"
    if not metadata_path.exists():
        raise FileNotFoundError(f"Paper metadata not found. Run 'just add-paper {paper_id}' first.")
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    paper_id_val = metadata.get("id", paper_id)

    mapping_path = paper_dir / "mapping.json"
    if mapping_path.exists():
        try:
            mapping = json.loads(mapping_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            mapping = {}
    else:
        mapping = {}

    namespace = mapping.get("namespace") or _default_namespace(paper_id_val)
    claim_to_decl = mapping.get("claim_to_decl")
    if not isinstance(claim_to_decl, dict):
        claim_to_decl = {}

    out = {
        "paper_id": paper_id_val,
        "namespace": namespace,
        "claim_to_decl": claim_to_decl,
    }
    mapping_path.write_text(json.dumps(out, indent=2), encoding="utf-8")


def _default_namespace(paper_id: str) -> str:
    """Default Lean namespace for a paper (safe identifier)."""
    safe = paper_id.replace("-", "_").replace(".", "_")
    return f"ScientificMemory.Papers.{safe}"
