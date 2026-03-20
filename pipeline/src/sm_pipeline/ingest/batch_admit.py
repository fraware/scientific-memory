"""Batch admit papers from CSV (SPEC 20): paper_id, domain, optional title, year."""

from __future__ import annotations

import csv
import json
from pathlib import Path

from sm_pipeline.ingest.admit_paper import admit_paper
from sm_pipeline.ingest.build_index import build_index

VALID_DOMAINS = frozenset(
    {
        "chemistry",
        "mathematics",
        "physics",
        "probability",
        "control",
        "quantum_information",
        "other",
    }
)


def _validate_row_domain(row: dict[str, str], paper_id: str) -> str:
    """Validate and return normalized domain from CSV row."""
    dom = (row.get("domain") or "other").strip()
    if dom not in VALID_DOMAINS:
        raise ValueError(f"Invalid domain {dom!r} for {paper_id}")
    return dom


def batch_admit_from_csv(repo_root: Path, csv_path: Path, dry_run: bool = False) -> list[str]:
    repo_root = Path(repo_root).resolve()
    admitted: list[str] = []
    with Path(csv_path).open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames or "paper_id" not in reader.fieldnames:
            raise ValueError("CSV must have header with paper_id")
        for row in reader:
            pid = (row.get("paper_id") or "").strip()
            if not pid:
                continue
            paper_dir = repo_root / "corpus" / "papers" / pid
            if not paper_dir.is_dir():
                if not dry_run:
                    admit_paper(repo_root, pid)
            # Validate domain in both dry_run and non-dry_run paths
            dom = _validate_row_domain(row, pid)
            if not dry_run:
                meta_path = paper_dir / "metadata.json"
                meta = json.loads(meta_path.read_text(encoding="utf-8"))
                meta["domain"] = dom
                if row.get("title"):
                    meta["title"] = row["title"].strip()
                if row.get("year"):
                    meta["year"] = int(row["year"])
                meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")
            admitted.append(pid)
    if not dry_run:
        build_index(repo_root)
    return admitted
