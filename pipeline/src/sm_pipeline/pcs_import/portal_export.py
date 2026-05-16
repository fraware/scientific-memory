"""Export PCS claims for the Next.js portal."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def build_pcs_portal_export(repo_root: Path) -> dict[str, Any]:
    root = repo_root.resolve()
    claims_dir = root / "corpus" / "pcs" / "claims"
    claims: dict[str, dict[str, Any]] = {}
    claim_ids: list[str] = []

    if claims_dir.is_dir():
        for claim_dir in sorted(claims_dir.iterdir()):
            if not claim_dir.is_dir():
                continue
            read_model_path = claim_dir / "read_model.json"
            if not read_model_path.is_file():
                continue
            data = json.loads(read_model_path.read_text(encoding="utf-8"))
            if not isinstance(data, dict):
                continue
            claim_id = str(data.get("claim_id") or claim_dir.name)
            claims[claim_id] = data
            claim_ids.append(claim_id)

    return {
        "schema_version": "PcsPortalExport.v0",
        "claim_ids": sorted(claim_ids),
        "claims": claims,
    }


def write_pcs_portal_export(repo_root: Path, claim_id: str | None = None) -> Path:
    """Write portal/.generated/pcs-export.json (all claims or validate one exists)."""
    root = repo_root.resolve()
    export = build_pcs_portal_export(root)
    if claim_id is not None and claim_id not in export["claims"]:
        raise FileNotFoundError(
            f"No imported PCS claim with id {claim_id!r}; run pcs-import-bundle first."
        )
    out_dir = root / "portal" / ".generated"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "pcs-export.json"
    out_path.write_text(json.dumps(export, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return out_path
