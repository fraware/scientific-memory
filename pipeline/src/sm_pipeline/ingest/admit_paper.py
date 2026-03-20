import json
from pathlib import Path

from sm_pipeline.ingest.build_index import build_index
from sm_pipeline.ingest.hash_source import hash_source_for_paper
from sm_pipeline.ingest.intake_report import write_intake_report


def admit_paper(repo_root: Path, paper_id: str) -> None:
    """Create paper directory skeleton with valid schema-conformant files."""
    base = repo_root / "corpus" / "papers" / paper_id
    base.mkdir(parents=True, exist_ok=True)
    (base / "source").mkdir(exist_ok=True)

    metadata = {
        "id": paper_id,
        "title": "(no title yet)",
        "authors": ["(unknown)"],
        "year": 1900,
        "domain": "other",
        "source": {
            "kind": "pdf",
            "path": f"corpus/papers/{paper_id}/source/source.pdf",
            "sha256": "0" * 64,
        },
        "artifact_status": "admitted",
    }
    (base / "metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    (base / "claims.json").write_text("[]", encoding="utf-8")
    (base / "assumptions.json").write_text("[]", encoding="utf-8")
    (base / "symbols.json").write_text("[]", encoding="utf-8")

    namespace = _default_namespace(paper_id)
    mapping = {
        "paper_id": paper_id,
        "namespace": namespace,
        "claim_to_decl": {},
    }
    (base / "mapping.json").write_text(json.dumps(mapping, indent=2), encoding="utf-8")

    build_hash = "0" * 64
    manifest = {
        "paper_id": paper_id,
        "version": "0.1.0",
        "build_hash": build_hash,
        "coverage_metrics": {
            "claim_count": 0,
            "mapped_claim_count": 0,
            "machine_checked_count": 0,
            "kernel_linked_count": 0,
        },
        "generated_pages": [],
    }
    (base / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    try:
        hash_source_for_paper(repo_root, paper_id)
    except (OSError, ValueError):
        pass
    try:
        build_index(repo_root)
    except OSError:
        pass
    try:
        write_intake_report(repo_root, paper_id)
    except OSError:
        pass


def _default_namespace(paper_id: str) -> str:
    """Default Lean namespace for a paper (safe identifier)."""
    safe = paper_id.replace("-", "_").replace(".", "_")
    return f"ScientificMemory.Papers.{safe}"
