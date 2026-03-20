"""Human-gated proof-repair apply (formal/ find-replace)."""

import json
from pathlib import Path

import pytest

from sm_pipeline.agentic.proof_repair_apply import apply_bundle, load_apply_bundle, preview_apply


def test_preview_apply_unique_match(tmp_path: Path) -> None:
    root = tmp_path
    lean = root / "formal" / "Demo.lean"
    lean.parent.mkdir(parents=True)
    lean.write_text("-- MARKER\n", encoding="utf-8")
    bundle_path = root / "bundle.json"
    bundle_path.write_text(
        json.dumps(
            {
                "verification_boundary": "human_review_only",
                "patches": [
                    {
                        "relative_path": "formal/Demo.lean",
                        "replacements": [{"find": "-- MARKER", "replace": "-- PATCHED"}],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    bundle = load_apply_bundle(bundle_path, root)
    rows = preview_apply(root, bundle)
    assert len(rows) == 1
    assert lean.read_text(encoding="utf-8") == "-- MARKER\n"
    modified = apply_bundle(root, bundle)
    assert modified == ["formal/Demo.lean"]
    assert lean.read_text(encoding="utf-8") == "-- PATCHED\n"


def test_apply_rejects_non_formal_path(tmp_path: Path) -> None:
    root = tmp_path
    bundle = {
        "verification_boundary": "human_review_only",
        "patches": [
            {
                "relative_path": "corpus/index.json",
                "replacements": [{"find": "x", "replace": "y"}],
            }
        ],
    }
    with pytest.raises(ValueError, match="formal"):
        preview_apply(root, bundle)


def test_apply_rejects_ambiguous_find(tmp_path: Path) -> None:
    root = tmp_path
    lean = root / "formal" / "X.lean"
    lean.parent.mkdir(parents=True)
    lean.write_text("a a\n", encoding="utf-8")
    bundle = {
        "verification_boundary": "human_review_only",
        "patches": [
            {
                "relative_path": "formal/X.lean",
                "replacements": [{"find": "a", "replace": "b"}],
            }
        ],
    }
    with pytest.raises(ValueError, match="matches"):
        preview_apply(root, bundle)
