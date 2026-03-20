"""Proof-repair / agentic interface tests (explicit verification boundaries)."""

from sm_pipeline.agentic.proof_repair import (
    INTERFACE_BOUNDARY,
    suggest_verification_boundary,
    VALID_BOUNDARIES,
)


def test_interface_boundary_is_human_review_only() -> None:
    """Agentic interface must be labeled human_review_only."""
    assert INTERFACE_BOUNDARY == "human_review_only"


def test_suggest_returns_interface_label() -> None:
    """Every suggestion carries the interface verification boundary."""
    out = suggest_verification_boundary(
        {"proof_status": "machine_checked", "verification_boundary": "fully_machine_checked"}
    )
    assert out["interface_verification_boundary"] == "human_review_only"


def test_suggest_preserves_valid_boundary() -> None:
    """Current valid boundary is suggested as-is."""
    out = suggest_verification_boundary(
        {"verification_boundary": "fully_machine_checked", "lean_decl": "Foo.bar"}
    )
    assert out["suggested_boundary"] == "fully_machine_checked"
    assert out["repair_hints"] == []


def test_suggest_fallback_for_unknown_boundary() -> None:
    """Unknown or empty boundary yields human_review_only."""
    out = suggest_verification_boundary({"verification_boundary": "unknown"})
    assert out["suggested_boundary"] == "human_review_only"
    out2 = suggest_verification_boundary({})
    assert out2["suggested_boundary"] == "human_review_only"


def test_suggested_boundary_in_valid_enum() -> None:
    """Suggested boundary is always one of the schema enum values."""
    for boundary in VALID_BOUNDARIES:
        out = suggest_verification_boundary({"verification_boundary": boundary})
        assert out["suggested_boundary"] in VALID_BOUNDARIES
