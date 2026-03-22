"""Canonical publication path keeps manifest and portal export aligned."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

from sm_pipeline.publish.canonical import publish_paper_artifacts


def test_publish_paper_artifacts_calls_manifest_then_export(tmp_path: Path, monkeypatch) -> None:
    calls: list[str] = []

    def fake_manifest(root: Path, paper_id: str) -> None:
        calls.append(f"manifest:{paper_id}")

    fake_export = MagicMock(return_value=tmp_path / "corpus-export.json")

    monkeypatch.setattr(
        "sm_pipeline.publish.canonical.publish_manifest",
        fake_manifest,
    )
    monkeypatch.setattr(
        "sm_pipeline.publish.canonical.export_portal_data",
        fake_export,
    )

    out = publish_paper_artifacts(tmp_path, "paper_a")
    assert calls == ["manifest:paper_a"]
    fake_export.assert_called_once_with(tmp_path.resolve())
    assert out["paper_id"] == "paper_a"
    assert "portal_export_path" in out
