"""Optional check: blueprint doc vs mapping.json claim_to_decl (SPEC 8.4)."""

import json
import re
from pathlib import Path


def check_paper_blueprint(repo_root: Path, paper_id: str) -> list[dict]:
    """
    If docs/blueprints/<paper_id>.md exists, parse claim ID and target decl from
    table rows; compare to corpus/papers/<paper_id>/mapping.json claim_to_decl.
    Return list of issues: {claim_id, kind: "missing"|"mismatch", expected?, actual?}.
    """
    repo_root = repo_root.resolve()
    blueprint_path = repo_root / "docs" / "blueprints" / f"{paper_id}.md"
    mapping_path = repo_root / "corpus" / "papers" / paper_id / "mapping.json"
    issues: list[dict] = []

    if not blueprint_path.exists():
        return issues
    if not mapping_path.exists():
        issues.append(
            {
                "paper_id": paper_id,
                "kind": "no_mapping",
                "message": "mapping.json not found",
            }
        )
        return issues

    blueprint_pairs = _parse_blueprint_table(blueprint_path)
    if not blueprint_pairs:
        return issues

    try:
        mapping = json.loads(mapping_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        issues.append(
            {
                "paper_id": paper_id,
                "kind": "invalid_mapping",
                "message": "mapping.json invalid",
            }
        )
        return issues

    claim_to_decl = (mapping.get("claim_to_decl") or {}) if isinstance(mapping, dict) else {}
    for claim_id, expected_decl in blueprint_pairs.items():
        actual = claim_to_decl.get(claim_id) if isinstance(claim_to_decl, dict) else None
        if actual is None:
            issues.append(
                {
                    "claim_id": claim_id,
                    "kind": "missing",
                    "expected_decl": expected_decl,
                }
            )
        elif actual != expected_decl:
            issues.append(
                {
                    "claim_id": claim_id,
                    "kind": "mismatch",
                    "expected_decl": expected_decl,
                    "actual_decl": actual,
                }
            )
    return issues


def _parse_blueprint_table(path: Path) -> dict[str, str]:
    """Extract claim_id -> target declaration from markdown table."""
    text = path.read_text(encoding="utf-8")
    pairs: dict[str, str] = {}
    lines = text.splitlines()
    for line in lines:
        if not line.strip().startswith("|") or "---" in line:
            continue
        parts = [p.strip() for p in line.split("|") if p.strip()]
        if len(parts) >= 2:
            claim_id = parts[0].strip()
            decl_cell = parts[1].strip()
            decl = re.sub(r"^`|`$", "", decl_cell)
            if claim_id and decl and not claim_id.lower().startswith("claim"):
                pairs[claim_id] = decl
    return pairs
