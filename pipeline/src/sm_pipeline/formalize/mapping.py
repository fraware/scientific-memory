"""Claim-to-Lean mapping helpers."""

from __future__ import annotations

import json
import re
from pathlib import Path


def generate_mapping(repo_root: Path, paper_id: str) -> dict:
    """
    Generate/update mapping.json for a paper using deterministic rules.

    Preference order for target declaration names:
    1) explicit short decl in claim.linked_formal_targets matching namespace
    2) last segment of linked_formal_targets
    3) normalized claim id suffix fallback
    """
    repo_root = repo_root.resolve()
    paper_dir = repo_root / "corpus" / "papers" / paper_id
    if not paper_dir.is_dir():
        raise FileNotFoundError(f"Paper directory not found: {paper_dir}")

    mapping_path = paper_dir / "mapping.json"
    existing = _read_json_object(mapping_path)
    namespace = str(existing.get("namespace") or _default_namespace(paper_id))
    claim_to_decl = (
        dict(existing.get("claim_to_decl"))
        if isinstance(existing.get("claim_to_decl"), dict)
        else {}
    )

    claims = _read_json_array(paper_dir / "claims.json")
    for claim in claims:
        claim_id = str(claim.get("id") or "").strip()
        if not claim_id:
            continue
        if claim_id in claim_to_decl and str(claim_to_decl[claim_id]).strip():
            continue
        short_decl = _infer_short_decl(claim, namespace)
        claim_to_decl[claim_id] = short_decl

    target_file = (existing.get("target_file") or "").strip() or _infer_target_file(namespace)
    output = {
        "paper_id": paper_id,
        "namespace": namespace,
        "claim_to_decl": dict(sorted(claim_to_decl.items())),
    }
    if target_file:
        output["target_file"] = target_file
    mapping_path.write_text(json.dumps(output, indent=2), encoding="utf-8")
    return output


def _infer_short_decl(claim: dict, namespace: str) -> str:
    targets = claim.get("linked_formal_targets") or []
    if isinstance(targets, list):
        for t in targets:
            target = str(t).strip()
            if not target:
                continue
            if namespace and target.startswith(namespace + "."):
                return target.removeprefix(namespace + ".")
            if "." in target:
                return target.split(".")[-1]
            return target
    claim_id = str(claim.get("id") or "claim")
    base = claim_id.split("_claim_")[-1] if "_claim_" in claim_id else claim_id
    return f"claim_{_to_lean_ident(base)}"


def _to_lean_ident(raw: str) -> str:
    s = raw.strip().lower()
    s = re.sub(r"[^a-z0-9]+", "_", s)
    s = re.sub(r"_+", "_", s).strip("_")
    if not s:
        return "unnamed"
    if s[0].isdigit():
        return f"c_{s}"
    return s


def _infer_target_file(namespace: str) -> str:
    """Infer Lean file path from namespace (e.g. ScientificMemory.Chemistry.Adsorption.Langmuir1918 -> formal/.../Langmuir1918.lean)."""
    if not (namespace or "").strip():
        return ""
    return f"formal/{namespace.replace('.', '/')}.lean"


def _default_namespace(paper_id: str) -> str:
    safe = paper_id.replace("-", "_").replace(".", "_")
    # Chemistry adsorption is the current wedge; fall back to Papers.*
    if "adsorption" in safe:
        domain = safe.split("_adsorption")[0]
        title = "".join(part.capitalize() for part in domain.split("_") if part)
        year = "".join(ch for ch in safe if ch.isdigit())[-4:] or "Paper"
        return f"ScientificMemory.Chemistry.Adsorption.{title}{year}"
    return f"ScientificMemory.Papers.{safe}"


def _read_json_array(path: Path) -> list[dict]:
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []
    if isinstance(data, list):
        return [x for x in data if isinstance(x, dict)]
    return []


def _read_json_object(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}
    if isinstance(data, dict):
        return data
    return {}
