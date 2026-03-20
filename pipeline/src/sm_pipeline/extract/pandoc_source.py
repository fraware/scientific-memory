"""Optional pandoc-based extraction from LaTeX/source (SPEC 6; ADR 0008). Non-gate."""

import json
import re
import shutil
import subprocess
from pathlib import Path


def check_pandoc_available() -> dict:
    """
    Detect if pandoc is available. Returns { "available": bool, "version": str | None }.
    """
    path = shutil.which("pandoc")
    if not path:
        return {"available": False, "version": None}
    try:
        out = subprocess.run(
            ["pandoc", "--version"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        first_line = (out.stdout or "").strip().split("\n")[0] if out.stdout else ""
        return {"available": out.returncode == 0, "version": first_line or None}
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return {"available": False, "version": None}


def extract_from_source(repo_root: Path, paper_id: str) -> Path | None:
    """
    If pandoc is available and corpus/papers/<paper_id>/source/main.tex exists,
    run pandoc to JSON and emit suggested claims (one per section heading) to
    corpus/papers/<paper_id>/suggested_claims.json. Does not overwrite claims.json.
    Returns path to suggested_claims.json if written, else None.
    """
    repo_root = repo_root.resolve()
    if not check_pandoc_available().get("available"):
        return None
    paper_dir = repo_root / "corpus" / "papers" / paper_id
    source_tex = paper_dir / "source" / "main.tex"
    if not source_tex.exists():
        return None
    try:
        result = subprocess.run(
            ["pandoc", str(source_tex), "-t", "json"],
            capture_output=True,
            text=True,
            timeout=60,
            cwd=repo_root,
        )
        if result.returncode != 0:
            return None
        doc = json.loads(result.stdout)
    except (subprocess.TimeoutExpired, json.JSONDecodeError, OSError):
        return None

    suggested = _suggest_claims_from_pandoc_json(doc, paper_id)
    out_path = paper_dir / "suggested_claims.json"
    out_path.write_text(json.dumps(suggested, indent=2), encoding="utf-8")
    return out_path


def _collect_math_from_blocks(blocks: list) -> list[tuple[int, str, str]]:
    """
    Walk blocks; return list of (section_index, math_type, content).
    section_index is 0-based (current section when we see the math).
    """
    result: list[tuple[int, str, str]] = []
    section_index = -1
    for block in blocks or []:
        if not isinstance(block, dict):
            continue
        t = block.get("t")
        c = block.get("c")
        if t == "Header":
            section_index += 1
            continue
        if t == "DisplayMath" and isinstance(c, list) and len(c) >= 1:
            content = c[0] if isinstance(c[0], str) else str(c[0])
            result.append((max(0, section_index), "DisplayMath", content))
            continue
        if t == "Para" and isinstance(c, list):
            for item in c:
                math_info = _math_from_inline(item)
                if math_info:
                    result.append((max(0, section_index), math_info[0], math_info[1]))
    return result


def _math_from_inline(node: dict) -> tuple[str, str] | None:
    """If node is Math, return (math_type, content); else None."""
    if not isinstance(node, dict) or node.get("t") != "Math":
        return None
    c = node.get("c")
    if not isinstance(c, list) or len(c) < 2:
        return None
    mt = c[0]
    content = c[1] if isinstance(c[1], str) else str(c[1])
    math_type = "InlineMath"
    if isinstance(mt, dict) and mt.get("t") == "DisplayMath":
        math_type = "DisplayMath"
    return (math_type, content)


def _symbols_from_math_content(content: str) -> list[str]:
    """Extract candidate symbol tokens from LaTeX math (e.g. \\theta, single letters)."""
    symbols: list[str] = []
    # Backslash-commands: \theta, \alpha, etc.
    for m in re.finditer(r"\\([a-zA-Z]+)", content):
        symbols.append(m.group(1))
    # Single-letter variables (common in math)
    for m in re.finditer(r"\b([a-zA-Z])\b", content):
        s = m.group(1)
        if s not in symbols:
            symbols.append(s)
    return symbols[:20]  # cap for sanity


def _suggest_claims_from_pandoc_json(doc: dict, paper_id: str) -> list:
    """
    Walk pandoc JSON (AST): one suggested claim per section heading; attach
    candidate_equations from Math nodes and optional candidate_symbols.
    """
    suggested = []
    if not isinstance(doc, dict):
        return suggested
    blocks = doc.get("blocks") or []
    section_num = 0
    for block in blocks:
        if not isinstance(block, dict):
            continue
        if block.get("t") == "Header":
            section_num += 1
            c = block.get("c")
            inlines = c[2] if isinstance(c, list) and len(c) > 2 else []
            text = _inline_to_string(inlines)
            if not text:
                continue
            suggested.append(
                {
                    "id": f"{paper_id}_suggested_{section_num}",
                    "paper_id": paper_id,
                    "section": str(section_num),
                    "informal_text": text[:500],
                    "claim_type": "editorial_exposition",
                    "status": "unparsed",
                    "candidate_equations": [],
                    "candidate_symbols": [],
                }
            )
    # Optional: collect macro context from RawBlocks (e.g. \newcommand in preamble)
    macro_context = _collect_macro_context_from_blocks(blocks)

    # Second pass: collect Math and assign to sections (by index)
    math_list = _collect_math_from_blocks(blocks)
    all_symbols = set()
    for sec_idx, math_type, content in math_list:
        if content and sec_idx < len(suggested):
            eq_entry = {"type": math_type, "content": content[:500]}
            suggested[sec_idx]["candidate_equations"].append(eq_entry)
            for sym in _symbols_from_math_content(content):
                all_symbols.add(sym)
                suggested[sec_idx]["candidate_symbols"] = list(
                    set(suggested[sec_idx]["candidate_symbols"]) | {sym}
                )[:15]
    # Attach macro context for human review; future tooling may use for expansion
    for s in suggested:
        s["macro_context"] = macro_context
    return suggested


def _collect_macro_context_from_blocks(blocks: list) -> list[dict]:
    """
    Collect \\newcommand and \\def from RawBlocks (latex/tex format).
    Returns list of { "name": str, "definition": str } for human review.
    No expansion; optional future step can use this for macro-derived content.
    """
    out: list[dict] = []
    seen: set[str] = set()
    for block in blocks or []:
        if not isinstance(block, dict) or block.get("t") != "RawBlock":
            continue
        c = block.get("c")
        if not isinstance(c, list) or len(c) < 2:
            continue
        fmt = (c[0] or "").lower()
        if fmt not in ("latex", "tex", "latex fragment"):
            continue
        text = c[1] if isinstance(c[1], str) else str(c[1])
        # \newcommand{\foo}{...} or \newcommand{\foo}[1]{...}
        for m in re.finditer(
            r"\\newcommand\s*\{\s*\\?([a-zA-Z]+)\s*\}(?:\[[^\]]*\])?\s*\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}",
            text,
        ):
            name, defn = m.group(1), m.group(2).strip()[:200]
            if name not in seen:
                seen.add(name)
                out.append({"name": name, "definition": defn})
        # \def\foo{...} (simple form)
        for m in re.finditer(r"\\def\s*\\?([a-zA-Z]+)\s*\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}", text):
            name, defn = m.group(1), m.group(2).strip()[:200]
            if name not in seen:
                seen.add(name)
                out.append({"name": name, "definition": defn})
    return out


def _inline_to_string(inlines: list) -> str:
    """Concatenate pandoc inline elements to plain text."""
    parts = []
    for x in inlines or []:
        if not isinstance(x, dict):
            continue
        if x.get("t") == "Str":
            parts.append(x.get("c", ""))
        elif x.get("t") == "Space":
            parts.append(" ")
    return "".join(parts).strip()
