"""8.3 Dimension suggestions: heuristic dimensional_metadata from kernels/symbols."""

import json
import re
from pathlib import Path


def compute_dimension_suggestions(repo_root: Path) -> dict:
    """
    Suggest dimensional_metadata for symbols that lack it (kernel constraints
    and name heuristics). Human triage only; no corpus edit.
    """
    repo_root = repo_root.resolve()
    papers_dir = repo_root / "corpus" / "papers"
    index_path = repo_root / "corpus" / "index.json"
    kernels_path = repo_root / "corpus" / "kernels.json"
    if not papers_dir.is_dir() or not index_path.exists():
        return _empty_result()

    index = json.loads(index_path.read_text(encoding="utf-8"))
    paper_ids = [
        p["id"] for p in (index.get("papers") or []) if isinstance(p, dict) and p.get("id")
    ]

    kernel_constraints: list[str] = []
    if kernels_path.exists():
        try:
            kernels = json.loads(kernels_path.read_text(encoding="utf-8"))
            if isinstance(kernels, list):
                for k in kernels:
                    if isinstance(k, dict):
                        for u in k.get("unit_constraints") or []:
                            if isinstance(u, str):
                                kernel_constraints.append(u)
        except (json.JSONDecodeError, OSError):
            pass

    suggestions: list[dict] = []
    for paper_id in paper_ids:
        symbols_path = papers_dir / paper_id / "symbols.json"
        if not symbols_path.exists():
            continue
        try:
            data = json.loads(symbols_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        if not isinstance(data, list):
            continue
        for s in data:
            if not isinstance(s, dict):
                continue
            if s.get("dimensional_metadata") and isinstance(s["dimensional_metadata"], dict):
                meta = s["dimensional_metadata"]
                has_unit_or_dim = meta.get("unit") or meta.get("dimension") or meta.get("kind")
                if has_unit_or_dim:
                    continue
            sid = s.get("id", "")
            normalized = (s.get("normalized_name") or "").strip()
            suggested = _suggest_for_symbol(normalized, sid, kernel_constraints)
            if suggested:
                suggestions.append(
                    {
                        "paper_id": paper_id,
                        "symbol_id": sid,
                        "suggested": suggested["suggested"],
                        "source": suggested["source"],
                    }
                )

    return {
        "dimension_suggestions": suggestions,
        "suggestion_count": len(suggestions),
    }


def _suggest_for_symbol(
    normalized_name: str, symbol_id: str, kernel_constraints: list[str]
) -> dict | None:
    """Return { suggested: { unit?, dimension?, kind? }, source } or None."""
    if not normalized_name:
        return None
    name_lower = normalized_name.lower()
    for constraint in kernel_constraints:
        if normalized_name in constraint or name_lower in constraint.lower():
            unit = _parse_unit_from_constraint(constraint)
            if unit:
                return {"suggested": {"unit": unit}, "source": "kernel"}
            if "in [0, 1]" in constraint or "dimensionless" in constraint:
                return {
                    "suggested": {"dimension": "dimensionless"},
                    "source": "kernel",
                }
    heuristic = _heuristic_dimension(normalized_name)
    if heuristic:
        return {"suggested": heuristic, "source": "heuristic"}
    return None


def _parse_unit_from_constraint(text: str) -> str | None:
    """Extract unit hint from constraint (e.g. 'K and P non-negative')."""
    if "non-negative" in text:
        return None
    m = re.search(r"\b(?:in|unit|as)\s+\[?([^\]]+)\]?", text, re.I)
    if m:
        return m.group(1).strip()[:80]
    return None


def _heuristic_dimension(normalized_name: str) -> dict | None:
    """Simple heuristics: common dimensionless symbols."""
    name = normalized_name.lower()
    dimensionless = {"theta", "alpha", "beta", "gamma", "coverage", "ratio"}
    if name in dimensionless or name.replace("_", "") in dimensionless:
        return {"dimension": "dimensionless", "kind": "dimensionless"}
    return None


def _empty_result() -> dict:
    return {
        "dimension_suggestions": [],
        "suggestion_count": 0,
    }
