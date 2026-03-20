"""Axiom and sorry count from Lean source (SPEC 12 formalization metrics)."""

import json
import re
from pathlib import Path


def _namespace_to_path_prefix(namespace: str) -> str:
    """Convert Lean namespace to path prefix under formal/ (A.B.C -> A/B/C)."""
    return namespace.replace(".", "/")


def _load_namespace_to_paper(repo_root: Path) -> dict[str, str]:
    """Build namespace -> paper_id from all corpus mapping.json files."""
    papers_dir = repo_root / "corpus" / "papers"
    if not papers_dir.is_dir():
        return {}
    result: dict[str, str] = {}
    for paper_dir in papers_dir.iterdir():
        if not paper_dir.is_dir():
            continue
        mapping_path = paper_dir / "mapping.json"
        if not mapping_path.exists():
            continue
        try:
            data = json.loads(mapping_path.read_text(encoding="utf-8"))
            if isinstance(data, dict) and data.get("namespace"):
                ns = str(data["namespace"]).strip()
                if ns:
                    result[ns] = str(paper_dir.name)
        except (json.JSONDecodeError, OSError):
            continue
    return result


def _paper_id_for_file(
    formal_dir: Path,
    path: Path,
    text: str,
    namespace_to_paper: dict[str, str],
) -> str | None:
    """
    Resolve paper_id for a .lean file by path or namespace declaration.
    Returns first matching paper_id or None if no mapping.
    """
    rel = path.relative_to(formal_dir)
    rel_str = str(rel).replace("\\", "/")

    for namespace, paper_id in namespace_to_paper.items():
        prefix = _namespace_to_path_prefix(namespace)
        if rel_str == prefix + ".lean" or rel_str.startswith(prefix + "/"):
            return paper_id

    namespace_re = re.compile(r"namespace\s+([A-Za-z0-9_.]+)")
    for m in namespace_re.finditer(text):
        ns = m.group(1).strip()
        if ns in namespace_to_paper:
            return namespace_to_paper[ns]
    return None


def compute_axiom_count(repo_root: Path) -> dict:
    """
    Scan formal/**/*.lean for axiom and sorry occurrences (word-boundary).
    Returns total counts, per-file breakdown, and per-paper breakdown when
    mapping.json namespace is available. Best-effort; not a full Lean AST.
    """
    repo_root = repo_root.resolve()
    formal_dir = repo_root / "formal"
    if not formal_dir.is_dir():
        return _empty_result()

    namespace_to_paper = _load_namespace_to_paper(repo_root)

    axiom_re = re.compile(r"\baxiom\b")
    sorry_re = re.compile(r"\bsorry\b")

    total_axiom = 0
    total_sorry = 0
    by_file: list[dict] = []
    by_paper: dict[str, dict] = {}
    files_scanned = 0

    for path in sorted(formal_dir.rglob("*.lean")):
        files_scanned += 1
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        rel = path.relative_to(formal_dir)
        axiom_count = len(axiom_re.findall(text))
        sorry_count = len(sorry_re.findall(text))
        total_axiom += axiom_count
        total_sorry += sorry_count
        if axiom_count or sorry_count:
            by_file.append(
                {
                    "file": str(rel),
                    "axiom_count": axiom_count,
                    "sorry_count": sorry_count,
                }
            )

        paper_id = (
            _paper_id_for_file(formal_dir, path, text, namespace_to_paper)
            if namespace_to_paper
            else None
        )
        if paper_id:
            if paper_id not in by_paper:
                by_paper[paper_id] = {
                    "axiom_count": 0,
                    "sorry_count": 0,
                    "files": [],
                }
            by_paper[paper_id]["axiom_count"] += axiom_count
            by_paper[paper_id]["sorry_count"] += sorry_count
            by_paper[paper_id]["files"].append(str(rel))

    result = {
        "total_axiom_count": total_axiom,
        "total_sorry_count": total_sorry,
        "by_file": by_file,
        "files_scanned": files_scanned,
    }
    if by_paper:
        result["by_paper"] = by_paper
    return result


def _empty_result() -> dict:
    return {
        "total_axiom_count": 0,
        "total_sorry_count": 0,
        "by_file": [],
        "files_scanned": 0,
    }
