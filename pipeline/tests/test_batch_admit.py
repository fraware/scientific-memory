"""Batch admit from CSV."""

import csv
from pathlib import Path

import pytest

from sm_pipeline.ingest.batch_admit import batch_admit_from_csv


def test_batch_admit_creates_and_updates(tmp_path: Path) -> None:
    root = tmp_path
    (root / "corpus").mkdir()
    (root / "corpus" / "index.json").write_text(
        '{"version":"0.1","papers":[]}', encoding="utf-8"
    )
    csv_path = root / "in.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["paper_id", "domain", "title", "year"])
        w.writeheader()
        w.writerow(
            {
                "paper_id": "batch_demo_a",
                "domain": "physics",
                "title": "Demo A",
                "year": "2025",
            }
        )
        w.writerow({"paper_id": "batch_demo_b", "domain": "chemistry"})
    ids = batch_admit_from_csv(root, csv_path)
    assert ids == ["batch_demo_a", "batch_demo_b"]
    idx = (root / "corpus" / "index.json").read_text(encoding="utf-8")
    assert "batch_demo_a" in idx
    meta = (root / "corpus" / "papers" / "batch_demo_a" / "metadata.json").read_text(
        encoding="utf-8"
    )
    assert "Demo A" in meta
    assert '"domain": "physics"' in meta


def test_batch_admit_dry_run(tmp_path: Path) -> None:
    """Test dry-run mode: validates CSV without writing files."""
    root = tmp_path
    (root / "corpus").mkdir()
    (root / "corpus" / "index.json").write_text(
        '{"version":"0.1","papers":[]}', encoding="utf-8"
    )
    csv_path = root / "in.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["paper_id", "domain"])
        w.writeheader()
        w.writerow({"paper_id": "dry_demo", "domain": "mathematics"})
    ids = batch_admit_from_csv(root, csv_path, dry_run=True)
    assert ids == ["dry_demo"]
    # Verify no files were created
    assert not (root / "corpus" / "papers" / "dry_demo").exists()
    # Verify index unchanged
    idx = (root / "corpus" / "index.json").read_text(encoding="utf-8")
    assert idx == '{"version":"0.1","papers":[]}'


def test_batch_admit_dry_run_invalid_domain(tmp_path: Path) -> None:
    """Test dry-run mode rejects invalid domain."""
    root = tmp_path
    (root / "corpus").mkdir()
    (root / "corpus" / "index.json").write_text(
        '{"version":"0.1","papers":[]}', encoding="utf-8"
    )
    csv_path = root / "in.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["paper_id", "domain"])
        w.writeheader()
        w.writerow({"paper_id": "invalid", "domain": "invalid_domain"})
    with pytest.raises(ValueError, match="Invalid domain"):
        batch_admit_from_csv(root, csv_path, dry_run=True)
