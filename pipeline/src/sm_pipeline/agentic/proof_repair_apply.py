"""
Apply human-reviewed proof-repair patches to Lean sources (formal/ only).

Never invoked from CI. Requires explicit CLI flags acknowledging human review.
"""

from __future__ import annotations

import json
from pathlib import Path

from jsonschema import validate


def _repo_root(repo_root: Path) -> Path:
    return Path(repo_root).resolve()


def _schemas_dir(repo_root: Path) -> Path:
    return _repo_root(repo_root) / "schemas"


def load_apply_bundle(path: Path, repo_root: Path) -> dict:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    schema_path = _schemas_dir(repo_root) / "proof_repair_apply_bundle.schema.json"
    if schema_path.is_file():
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        validate(instance=data, schema=schema)
    return data


def preview_apply(repo_root: Path, bundle: dict) -> list[tuple[str, str, str]]:
    """
    Returns list of (relative_path, before_snippet, after_snippet) for each replacement.
    Does not write files.
    """
    root = _repo_root(repo_root)
    out: list[tuple[str, str, str]] = []
    for patch in bundle.get("patches") or []:
        rel = (patch.get("relative_path") or "").replace("\\", "/").strip()
        if not rel.startswith("formal/") or ".." in rel:
            raise ValueError(f"Invalid or unsafe path (must stay under formal/): {rel!r}")
        fpath = (root / rel).resolve()
        if not str(fpath).startswith(str(root / "formal")):
            raise ValueError(f"Path escapes formal/: {rel!r}")
        if not fpath.is_file():
            raise FileNotFoundError(f"Missing file: {rel}")
        text = fpath.read_text(encoding="utf-8")
        for rep in patch.get("replacements") or []:
            find = rep.get("find")
            replace = rep.get("replace", "")
            if not find or not isinstance(find, str):
                raise ValueError("Each replacement needs non-empty find string")
            count = text.count(find)
            if count == 0:
                raise ValueError(f"find string not found in {rel!r}")
            if count > 1:
                raise ValueError(
                    f"find string matches {count} times in {rel!r}; use a unique snippet"
                )
            new_text = text.replace(find, replace, 1)
            # unified-diff style one hunk for typer output
            out.append(
                (
                    rel,
                    find[:200] + ("..." if len(find) > 200 else ""),
                    replace[:200] + ("..." if len(replace) > 200 else ""),
                )
            )
            text = new_text
    return out


def apply_bundle(repo_root: Path, bundle: dict) -> list[str]:
    """Apply patches in place. Returns list of modified relative paths."""
    root = _repo_root(repo_root)
    modified: list[str] = []
    for patch in bundle.get("patches") or []:
        rel = (patch.get("relative_path") or "").replace("\\", "/").strip()
        if not rel.startswith("formal/") or ".." in rel:
            raise ValueError(f"Invalid or unsafe path: {rel!r}")
        fpath = (root / rel).resolve()
        if not str(fpath).startswith(str(root / "formal")):
            raise ValueError(f"Path escapes formal/: {rel!r}")
        text = fpath.read_text(encoding="utf-8")
        orig = text
        for rep in patch.get("replacements") or []:
            find = rep.get("find")
            replace = rep.get("replace", "")
            if not find:
                raise ValueError("Empty find")
            if text.count(find) != 1:
                raise ValueError(f"Expected exactly one match in {rel}")
            text = text.replace(find, replace, 1)
        if text != orig:
            fpath.write_text(text, encoding="utf-8", newline="\n")
            modified.append(rel)
    return modified
