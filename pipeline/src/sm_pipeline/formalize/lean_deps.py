"""
Extract declaration-level dependencies from Lean source for theorem cards.

Parses .lean files to find references from one declaration to another within the same
file; only declarations that appear in the paper's theorem cards are considered.
Populates theorem_cards[].dependency_ids (card IDs) so manifest.dependency_graph can be non-empty.
"""

from __future__ import annotations

import re
from pathlib import Path


def _short_name(lean_decl: str) -> str:
    """Return the last segment of a fully qualified declaration name."""
    return lean_decl.split(".")[-1] if lean_decl else ""


def _parse_lean_declarations_and_bodies(content: str) -> list[tuple[str, str]]:
    """
    Parse Lean file content into (decl_short_name, body) pairs.
    Declarations are theorem/def/noncomputable def; body is text after := until next decl or end.
    """
    # Match start of declaration: (theorem|def|noncomputable def) optionally with attributes, then name
    decl_start = re.compile(
        r"^(?:@\[[\w\s,]+\]\s+)?(?:theorem|def|noncomputable\s+def)\s+([a-zA-Z][a-zA-Z0-9_']*)",
        re.MULTILINE,
    )
    pairs: list[tuple[str, str]] = []
    for m in decl_start.finditer(content):
        name = m.group(1)
        start = m.end()
        # Find body: after first := on this line or next lines until we hit next declaration or end
        rest = content[start:]
        eq_pos = rest.find(":=")
        if eq_pos == -1:
            continue
        body_start = start + eq_pos + 2
        body_rest = content[body_start:]
        # Heuristic: body ends at next decl start (same pattern) or at "end Namespace"
        next_decl = decl_start.search(body_rest)
        end_match = re.search(r"^\s*end\s+", body_rest, re.MULTILINE)
        end_pos = len(body_rest)
        if next_decl:
            end_pos = min(end_pos, next_decl.start())
        if end_match:
            end_pos = min(end_pos, end_match.start())
        body = body_rest[:end_pos]
        pairs.append((name, body))
    return pairs


def _find_referenced_declarations(body: str, candidate_short_names: set[str]) -> set[str]:
    """Find which of candidate_short_names appear as identifiers in body (word-boundary)."""
    found: set[str] = set()
    for name in candidate_short_names:
        # Match as whole word (identifier), avoid matching as substring of longer name
        pattern = r"(?<![a-zA-Z0-9_'])(" + re.escape(name) + r")(?![a-zA-Z0-9_'])"
        if re.search(pattern, body):
            found.add(name)
    return found


def extract_dependency_ids_for_cards(
    repo_root: Path, paper_id: str, cards: list[dict]
) -> list[dict]:
    """
    For each card, populate dependency_ids from Lean source: which other cards' declarations
    are referenced in this declaration's proof/body. Only same-file, same-paper cards count.
    Returns new list of cards with dependency_ids set (mutates and returns).
    """
    repo_root = repo_root.resolve()
    if not cards:
        return cards

    # Build lean_decl (full) -> card_id, and per file_path set of (short_name, card_id)
    decl_to_card: dict[str, str] = {}
    file_to_decls: dict[str, list[tuple[str, str]]] = {}  # file_path -> [(short_name, card_id)]
    for c in cards:
        if not isinstance(c, dict):
            continue
        card_id = c.get("id")
        lean_decl = (c.get("lean_decl") or "").strip()
        file_path = (c.get("file_path") or "").strip()
        if not card_id or not lean_decl or not file_path:
            continue
        short = _short_name(lean_decl)
        decl_to_card[lean_decl] = card_id
        file_to_decls.setdefault(file_path, []).append((short, card_id))

    # Per file: read source, parse declarations and bodies, resolve references to card IDs
    for file_path, decl_list in file_to_decls.items():
        path = repo_root / file_path
        if not path.exists():
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except (OSError, ValueError):
            continue
        candidate_short_names = {d[0] for d in decl_list}
        short_to_card = {d[0]: d[1] for d in decl_list}
        pairs = _parse_lean_declarations_and_bodies(content)
        decl_body: dict[str, str] = {name: body for name, body in pairs}
        for short_name, card_id in decl_list:
            body = decl_body.get(short_name, "")
            refs = _find_referenced_declarations(body, candidate_short_names - {short_name})
            dep_ids = sorted({short_to_card[r] for r in refs if short_to_card.get(r)})
            for c in cards:
                if isinstance(c, dict) and c.get("id") == card_id:
                    c["dependency_ids"] = dep_ids
                    break
    for c in cards:
        if isinstance(c, dict):
            c.setdefault("dependency_extraction_method", "lean_source_regex_tier0")
    return cards
