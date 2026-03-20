"""Write extraction_run.json per paper: extraction metrics as persistent record (SPEC 8.2)."""

import json
from datetime import UTC, datetime
from pathlib import Path


def write_extraction_run(repo_root: Path, paper_id: str) -> Path:
    """
    Write corpus/papers/<paper_id>/extraction_run.json with claim_count,
    claims_with_source_span, assumption_count, recorded_at.
    Optional artifact; not required by validation.
    """
    repo_root = repo_root.resolve()
    paper_dir = repo_root / "corpus" / "papers" / paper_id
    if not paper_dir.is_dir():
        raise FileNotFoundError(f"Paper directory not found: {paper_dir}")

    claims_path = paper_dir / "claims.json"
    assumptions_path = paper_dir / "assumptions.json"

    claim_count = 0
    claims_with_source_span = 0
    if claims_path.exists():
        try:
            claims = json.loads(claims_path.read_text(encoding="utf-8"))
            if isinstance(claims, list):
                claim_count = len(claims)
                for c in claims:
                    if not isinstance(c, dict):
                        continue
                    span = c.get("source_span")
                    if (
                        isinstance(span, dict)
                        and span.get("source_file")
                        and span.get("start")
                        and span.get("end")
                    ):
                        claims_with_source_span += 1
        except (json.JSONDecodeError, OSError):
            pass

    assumption_count = 0
    if assumptions_path.exists():
        try:
            raw = assumptions_path.read_text(encoding="utf-8")
            assumptions = json.loads(raw)
            if isinstance(assumptions, list):
                assumption_count = len(assumptions)
        except (json.JSONDecodeError, OSError):
            pass

    now = datetime.now(UTC)
    recorded_at = now.isoformat(timespec="seconds").replace("+00:00", "Z")
    payload = {
        "paper_id": paper_id,
        "recorded_at": recorded_at,
        "claim_count": claim_count,
        "claims_with_source_span": claims_with_source_span,
        "assumption_count": assumption_count,
    }
    out_path = paper_dir / "extraction_run.json"
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return out_path
