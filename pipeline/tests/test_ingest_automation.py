"""Ingest automation tests for hash-source and build-index."""

import json
import tempfile
from pathlib import Path

from sm_pipeline.ingest.build_index import build_index
from sm_pipeline.ingest.hash_source import hash_source_for_paper


def test_hash_source_updates_metadata_sha256() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        paper_dir = root / "corpus" / "papers" / "p1"
        source_dir = paper_dir / "source"
        source_dir.mkdir(parents=True)
        source_path = source_dir / "source.pdf"
        source_path.write_bytes(b"abc123")
        metadata = {
            "id": "p1",
            "title": "T",
            "authors": ["A"],
            "year": 2000,
            "domain": "other",
            "source": {
                "kind": "pdf",
                "path": "corpus/papers/p1/source/source.pdf",
                "sha256": "0" * 64,
            },
            "artifact_status": "admitted",
        }
        (paper_dir / "metadata.json").write_text(json.dumps(metadata), encoding="utf-8")

        digest = hash_source_for_paper(root, "p1")
        updated = json.loads((paper_dir / "metadata.json").read_text(encoding="utf-8"))
        assert digest == updated["source"]["sha256"]
        assert digest != "0" * 64


def test_build_index_collects_metadata_entries() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        papers_dir = root / "corpus" / "papers"
        (papers_dir / "p1").mkdir(parents=True)
        (papers_dir / "p2").mkdir(parents=True)
        (papers_dir / "p1" / "metadata.json").write_text(
            json.dumps(
                {
                    "id": "p1",
                    "title": "Paper One",
                    "authors": ["A"],
                    "year": 1918,
                    "domain": "chemistry",
                    "source": {"kind": "pdf", "path": "x", "sha256": "0" * 64},
                    "artifact_status": "admitted",
                }
            ),
            encoding="utf-8",
        )
        (papers_dir / "p2" / "metadata.json").write_text(
            json.dumps(
                {
                    "id": "p2",
                    "title": "Paper Two",
                    "authors": ["B"],
                    "year": 1906,
                    "domain": "chemistry",
                    "source": {"kind": "pdf", "path": "y", "sha256": "0" * 64},
                    "artifact_status": "admitted",
                }
            ),
            encoding="utf-8",
        )

        out = build_index(root)
        payload = json.loads(out.read_text(encoding="utf-8"))
        assert payload["version"] == "0.1"
        ids = [p["id"] for p in payload["papers"]]
        assert ids == ["p1", "p2"]
