"""Write intake_report.json per paper: initial parsing report (SPEC 8.1)."""

import json
from datetime import UTC, datetime
from pathlib import Path


def write_intake_report(repo_root: Path, paper_id: str) -> Path:
    """
    Write corpus/papers/<paper_id>/intake_report.json with paper_id,
    created_at (ISO), source_files_found (list of paths under source/).
    Optional artifact; satisfies "initial parsing report" in minimal form.
    """
    repo_root = repo_root.resolve()
    paper_dir = repo_root / "corpus" / "papers" / paper_id
    if not paper_dir.is_dir():
        raise FileNotFoundError(f"Paper directory not found: {paper_dir}")

    source_dir = paper_dir / "source"
    source_files_found: list[str] = []
    if source_dir.is_dir():
        for p in source_dir.iterdir():
            if p.is_file():
                source_files_found.append(p.name)

    now = datetime.now(UTC)
    created_at = now.isoformat(timespec="seconds").replace("+00:00", "Z")
    payload = {
        "paper_id": paper_id,
        "created_at": created_at,
        "source_files_found": source_files_found,
    }
    out_path = paper_dir / "intake_report.json"
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return out_path
