"""Collect plain-text context from a paper directory for LLM prompts."""

from __future__ import annotations

import json
from pathlib import Path

_TEXT_SUFFIXES = {".md", ".txt", ".tex", ".bib"}


def gather_paper_source_text(paper_dir: Path, max_chars: int = 120_000) -> str:
    """Concatenate readable files under `source/` (best-effort)."""
    source_root = paper_dir / "source"
    if not source_root.is_dir():
        return ""
    parts: list[str] = []
    total = 0
    for path in sorted(source_root.rglob("*")):
        if not path.is_file():
            continue
        if path.suffix.lower() not in _TEXT_SUFFIXES:
            continue
        try:
            raw = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        rel = path.relative_to(paper_dir).as_posix()
        chunk = f"\n\n--- file: {rel} ---\n\n{raw}"
        if total + len(chunk) > max_chars:
            chunk = chunk[: max(0, max_chars - total)]
        parts.append(chunk)
        total += len(chunk)
        if total >= max_chars:
            break
    return "".join(parts).strip()


def load_json_if_exists(path: Path) -> object | None:
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
