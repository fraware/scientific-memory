"""Portal read model bundle shape."""

import json
from pathlib import Path

from sm_pipeline.publish.portal_read_model import build_portal_bundle


def test_build_portal_bundle_has_expected_keys() -> None:
    repo = Path(__file__).resolve().parents[2]
    bundle = build_portal_bundle(repo)
    assert bundle["version"] == "0.1"
    assert "papers_index" in bundle
    assert "papers" in bundle
    assert "kernels" in bundle
    assert isinstance(bundle["papers"], dict)
    # At least one paper from real corpus
    if bundle["papers"]:
        pid = next(iter(bundle["papers"]))
        paper = bundle["papers"][pid]
        assert "manifest" in paper
        assert "claims" in paper


def test_build_portal_bundle_matches_export_shape(tmp_path: Path) -> None:
    """Exported JSON should deserialize to same top-level keys as build_portal_bundle."""
    repo = Path(__file__).resolve().parents[2]
    export_path = repo / "portal" / ".generated" / "corpus-export.json"
    if not export_path.exists():
        return
    raw = json.loads(export_path.read_text(encoding="utf-8"))
    built = build_portal_bundle(repo)
    assert set(raw.keys()) == set(built.keys())
