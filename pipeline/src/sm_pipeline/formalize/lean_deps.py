"""
Extract declaration-level dependencies from Lean source for theorem cards.

Parses .lean files to find references from one declaration to another within the same
file. Only declarations that appear in the paper's theorem cards are considered.
Populates theorem_cards[].dependency_ids (card IDs) so manifest.dependency_graph can
be non-empty.
"""

from __future__ import annotations

import re
from pathlib import Path


def _short_name(lean_decl: str) -> str:
    """Return the last segment of a fully qualified declaration name."""
    return lean_decl.split(".")[-1] if lean_decl else ""


def _strip_lean_comments(content: str) -> str:
    """Remove Lean comments to reduce false positive dependency matches."""

    # Remove block comments first, then line comments.
    # This is a best-effort regex stripper; it is designed for extraction stability,
    # not perfect parsing.
    content = re.sub(r"/-.*?-/", "", content, flags=re.DOTALL)
    content = re.sub(r"--.*?$", "", content, flags=re.MULTILINE)
    return content


def _decl_start_regex() -> re.Pattern[str]:
    """
    Match Lean theorem/def declarations with optional attribute blocks.

    We intentionally accept multiple attribute lines immediately preceding the declaration.
    """

    return re.compile(
        r"^(?:\s*@\[[^\n]*\]\s*)*"
        r"(?:theorem|lemma|def|noncomputable\s+def)\s+"
        r"([a-zA-Z][a-zA-Z0-9_']*)",
        re.MULTILINE,
    )


def _parse_lean_declarations_and_bodies(content: str) -> list[tuple[str, str]]:
    """
    Parse Lean file content into (decl_short_name, body) pairs.
    Declarations are theorem/def/noncomputable def; body is text after := until next decl or end.
    """
    # Match start of declaration: (theorem|def|noncomputable def) optionally with attributes, then name
    decl_start = _decl_start_regex()
    pairs: list[tuple[str, str]] = []
    for m in decl_start.finditer(content):
        name = m.group(1)
        start = m.end()
        # Find body: after the first := on this line (or subsequent lines) until
        # we hit the next declaration or end.
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


_FQ_DECL_PATTERN = re.compile(r"\bScientificMemory\.(?:[A-Za-z0-9_][A-Za-z0-9_.']*)\b")


def _find_fq_scientificmemory_refs(body: str, decl_to_card: dict[str, str]) -> set[str]:
    """Resolve fully qualified ScientificMemory.* names in proof bodies to card ids."""
    out: set[str] = set()
    for m in _FQ_DECL_PATTERN.finditer(body):
        fq = m.group(0)
        cid = decl_to_card.get(fq)
        if cid:
            out.add(cid)
    return out


def _collect_rhs_to_def_short_names(content: str) -> dict[str, set[str]]:
    """
    Map RHS identifier (e.g. LangmuirCoverage) to local def short names that alias it.

    Matches `def foo := Bar` / `noncomputable def foo := Bar` where Bar is a single
    identifier (common pattern for isotherm definitions referencing a shared symbol).
    """
    out: dict[str, set[str]] = {}
    pat = re.compile(
        r"(?:noncomputable\s+def|def)\s+([a-zA-Z][a-zA-Z0-9_']*)\s*:=\s*"
        r"([a-zA-Z][a-zA-Z0-9_']*)\s*(?:\n|$)",
        re.MULTILINE,
    )
    for m in pat.finditer(content):
        short, rhs = m.group(1), m.group(2)
        out.setdefault(rhs, set()).add(short)
    return out


def _deps_from_rhs_symbol_mentions(
    body: str,
    rhs_to_def_shorts: dict[str, set[str]],
    unique_short_to_card: dict[str, str],
    self_short: str,
    self_card_id: str,
) -> set[str]:
    """When a proof mentions a symbol (e.g. FreundlichIsotherm), link to its local def card."""
    out: set[str] = set()
    for rhs, def_shorts in rhs_to_def_shorts.items():
        pat = r"(?<![a-zA-Z0-9_'])(" + re.escape(rhs) + r")(?![a-zA-Z0-9_'])"
        if not re.search(pat, body):
            continue
        for s in def_shorts:
            if s == self_short:
                continue
            cid = unique_short_to_card.get(s)
            if cid and str(cid) != str(self_card_id):
                out.add(str(cid))
    return out


def _deps_from_unfold_prefix(
    body: str,
    unique_short_to_card: dict[str, str],
    self_short: str,
    self_card_id: str,
) -> set[str]:
    """
    Link `unfold foo` to the best-matching card short name (e.g. unfold temkin_theta -> temkin_theta_eq).
    """
    out: set[str] = set()
    for m in re.finditer(r"\bunfold\s+([a-zA-Z][a-zA-Z0-9_']*)", body):
        u = m.group(1)
        if u == self_short:
            continue
        best: str | None = None
        for s in unique_short_to_card:
            if s == self_short:
                continue
            if s.startswith(u) and len(s) >= len(u):
                if best is None or len(s) < len(best):
                    best = s
        if best:
            cid = unique_short_to_card.get(best)
            if cid and str(cid) != str(self_card_id):
                out.add(str(cid))
    return out


def _body_is_ring_only_proof(body: str) -> bool:
    """True when the proof is just `by ring` (kinematics-style algebraic lemmas)."""
    s = body.strip()
    if not s:
        return False
    return re.match(r"^by\s+ring\s*$", s, re.DOTALL) is not None


def extract_dependency_ids_for_cards(
    repo_root: Path, paper_id: str, cards: list[dict]
) -> list[dict]:
    """
    For each card, populate dependency_ids from Lean source: which other cards'
    declarations are referenced in this declaration's proof/body.
    Only same-file (same paper), same-paper cards count.
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
        decl_to_card[lean_decl] = str(card_id)
        file_to_decls.setdefault(file_path, []).append((short, card_id))

    # Per file: read source, parse declarations and bodies, resolve references to card IDs
    # Candidate resolution across files within the same paper:
    # - If a short name maps uniquely to one card_id, allow it as a dependency reference across files.
    # - If the short name is ambiguous, we skip it conservatively.
    short_to_card_ids: dict[str, set[str]] = {}
    for c in cards:
        if not isinstance(c, dict):
            continue
        lean_decl = (c.get("lean_decl") or "").strip()
        card_id = c.get("id")
        if not lean_decl or not card_id:
            continue
        short = _short_name(lean_decl)
        short_to_card_ids.setdefault(short, set()).add(str(card_id))

    unique_short_to_card: dict[str, str] = {
        short: next(iter(ids)) for short, ids in short_to_card_ids.items() if len(ids) == 1
    }

    candidate_short_names_all = set(unique_short_to_card.keys())

    for file_path, decl_list in file_to_decls.items():
        path = repo_root / file_path
        if not path.exists():
            continue
        try:
            content = _strip_lean_comments(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        short_to_card = unique_short_to_card
        pairs = _parse_lean_declarations_and_bodies(content)
        decl_body: dict[str, str] = {name: body for name, body in pairs}
        rhs_to_def_shorts = _collect_rhs_to_def_short_names(content)
        decl_order = [name for name, _ in pairs]
        prev_short_for: dict[str, str | None] = {}
        prev: str | None = None
        for name in decl_order:
            prev_short_for[name] = prev
            prev = name
        for short_name, card_id in decl_list:
            body = decl_body.get(short_name, "")
            refs = _find_referenced_declarations(body, candidate_short_names_all - {short_name})
            dep_ids_short = {short_to_card[r] for r in refs if short_to_card.get(r)}
            dep_ids_fq = _find_fq_scientificmemory_refs(body, decl_to_card)
            dep_ids_alias = _deps_from_rhs_symbol_mentions(
                body,
                rhs_to_def_shorts,
                short_to_card,
                short_name,
                str(card_id),
            )
            dep_ids_unfold = _deps_from_unfold_prefix(
                body,
                short_to_card,
                short_name,
                str(card_id),
            )
            merged = dep_ids_short | dep_ids_fq | dep_ids_alias | dep_ids_unfold
            merged.discard(str(card_id))
            if not merged and _body_is_ring_only_proof(body):
                p = prev_short_for.get(short_name)
                if p and p in short_to_card:
                    ps = short_to_card[p]
                    if ps != str(card_id):
                        merged.add(ps)
            dep_ids = sorted(merged)
            method = "lean_source_regex_tier0"
            if dep_ids_fq or dep_ids_alias or dep_ids_unfold:
                method = "lean_source_regex_tier1"
            for c in cards:
                if isinstance(c, dict) and c.get("id") == card_id:
                    c["dependency_ids"] = dep_ids
                    c["dependency_extraction_method"] = method
                    break
    for c in cards:
        if isinstance(c, dict) and "dependency_extraction_method" not in c:
            c.setdefault("dependency_extraction_method", "lean_source_regex_tier0")
    return cards
