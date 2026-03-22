"""Canonical portal read model: build bundle dict for export.

SPEC intent: schema-first portal data projection.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

# Single source for the portal export schema version string
# (keep in sync with portal consumers).
PORTAL_BUNDLE_VERSION = "0.3"


def load_paper_bundle(repo_root: Path, paper_id: str) -> dict[str, Any]:
    """Load all JSON artifacts for one paper into a single dict."""
    repo_root = repo_root.resolve()
    paper_dir = repo_root / "corpus" / "papers" / paper_id
    return {
        "metadata": _read_json_object(paper_dir / "metadata.json"),
        "claims": _read_json_array(paper_dir / "claims.json"),
        "assumptions": _read_json_array(paper_dir / "assumptions.json"),
        "symbols": _read_json_array(paper_dir / "symbols.json"),
        "mapping": _read_json_object(paper_dir / "mapping.json"),
        "manifest": _read_json_object(paper_dir / "manifest.json"),
        "theorem_cards": _read_json_array(paper_dir / "theorem_cards.json"),
    }


def build_portal_bundle(repo_root: Path) -> dict[str, Any]:
    """
    Build the full portal export structure
    (version, papers_index, papers map, kernels).
    This is the single projection used by export_portal_data.
    """
    repo_root = repo_root.resolve()
    papers_index = _read_json_object(repo_root / "corpus" / "index.json")
    papers = papers_index.get("papers") or []
    paper_map: dict[str, dict[str, Any]] = {}
    claim_id_to_paper_id: dict[str, str] = {}
    claim_id_to_claim: dict[str, dict[str, Any]] = {}
    theorem_card_id_to_paper_id: dict[str, str] = {}
    theorem_card_id_to_card: dict[str, dict[str, Any]] = {}
    declaration_to_theorem_card_id: dict[str, str] = {}
    kernel_id_to_kernel: dict[str, dict[str, Any]] = {}
    kernel_id_to_paper_ids: dict[str, list[str]] = {}
    if isinstance(papers, list):
        for p in papers:
            if not isinstance(p, dict):
                continue
            paper_id = str(p.get("id") or "").strip()
            if not paper_id:
                continue
            pb = load_paper_bundle(repo_root, paper_id)
            paper_map[paper_id] = pb

            for c in pb.get("claims") or []:
                if not isinstance(c, dict):
                    continue
                cid = str(c.get("id") or "").strip()
                if not cid:
                    continue
                claim_id_to_paper_id[cid] = paper_id
                claim_id_to_claim[cid] = c

            for card in pb.get("theorem_cards") or []:
                if not isinstance(card, dict):
                    continue
                card_id = str(card.get("id") or "").strip()
                if not card_id:
                    continue
                theorem_card_id_to_paper_id[card_id] = paper_id
                theorem_card_id_to_card[card_id] = card
                lean_decl = str(card.get("lean_decl") or "").strip()
                if lean_decl:
                    declaration_to_theorem_card_id.setdefault(lean_decl, card_id)

            manifest = pb.get("manifest") or {}
            if isinstance(manifest, dict):
                for kid in manifest.get("kernel_index") or []:
                    kid_str = str(kid or "").strip()
                    if not kid_str:
                        continue
                    kernel_id_to_paper_ids.setdefault(kid_str, [])
                    if paper_id not in kernel_id_to_paper_ids[kid_str]:
                        kernel_id_to_paper_ids[kid_str].append(paper_id)

    kernels = _read_json_array(repo_root / "corpus" / "kernels.json")
    for k in kernels:
        if not isinstance(k, dict):
            continue
        kid = str(k.get("id") or "").strip()
        if not kid:
            continue
        kernel_id_to_kernel[kid] = k

    # Reverse index for fast theorem-card -> kernel navigation.
    theorem_card_id_to_kernel_ids: dict[str, list[str]] = {}
    for kid, kernel in kernel_id_to_kernel.items():
        linked = kernel.get("linked_theorem_cards") or []
        if not isinstance(linked, list):
            continue
        for card_id in linked:
            card_id_str = str(card_id or "").strip()
            if not card_id_str:
                continue
            theorem_card_id_to_kernel_ids.setdefault(card_id_str, [])
            if kid not in theorem_card_id_to_kernel_ids[card_id_str]:
                theorem_card_id_to_kernel_ids[card_id_str].append(kid)

    all_claim_ids = sorted(claim_id_to_paper_id.keys())
    # Card id and full lean_decl both work in getTheoremCardById / static routes.
    all_theorem_card_route_ids = sorted(
        set(theorem_card_id_to_paper_id.keys()) | set(declaration_to_theorem_card_id.keys())
    )

    return {
        "version": PORTAL_BUNDLE_VERSION,
        "papers_index": papers_index,
        "papers": paper_map,
        "kernels": kernels,
        "indices": {
            "claim_id_to_paper_id": claim_id_to_paper_id,
            "claim_id_to_claim": claim_id_to_claim,
            "theorem_card_id_to_paper_id": theorem_card_id_to_paper_id,
            "theorem_card_id_to_card": theorem_card_id_to_card,
            "declaration_to_theorem_card_id": declaration_to_theorem_card_id,
            "kernel_id_to_kernel": kernel_id_to_kernel,
            "kernel_id_to_paper_ids": kernel_id_to_paper_ids,
            "theorem_card_id_to_kernel_ids": theorem_card_id_to_kernel_ids,
            "all_claim_ids": all_claim_ids,
            "all_theorem_card_route_ids": all_theorem_card_route_ids,
        },
    }


def _read_json_array(path: Path) -> list:
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []
    return data if isinstance(data, list) else []


def _read_json_object(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}
    return data if isinstance(data, dict) else {}
