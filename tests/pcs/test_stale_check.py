"""Stale check payload helpers."""

from __future__ import annotations

from sm_pipeline.pcs_import.stale_check import build_stale_check_result


def test_build_stale_check_result_normalizes_reasons() -> None:
    payload = build_stale_check_result(
        "claim-pcs-qc-release-v0.1",
        {
            "stale": True,
            "stale_reasons": ["signed_bundle_hash changed"],
        },
    )
    assert payload["stale"] is True
    assert payload["stale_reasons"] == ["signed_bundle_hash_changed"]
    assert "Re-import the current release manifest" in payload["repair_hint"]
