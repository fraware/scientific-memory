"""Unit tests for PCS placeholder provenance detection."""

from sm_pipeline.pcs_validate.placeholder_commits import (
    is_local_dev_marker,
    is_placeholder_commit,
    validate_source_commit_for_release,
)


def test_placeholder_commit_patterns() -> None:
    for commit in (
        "a" * 40,
        "c" * 40,
        "0" * 40,
    ):
        assert is_placeholder_commit(commit)


def test_real_commit_is_not_placeholder() -> None:
    assert not is_placeholder_commit("993a0e5d1214b7c1bd6e84475d771806950965dd")


def test_local_dev_marker_rejected() -> None:
    assert is_local_dev_marker("local-dev")
    msg = validate_source_commit_for_release("993a0e5d1214b7c1bd6e84475d771806950965dd", path="x", local_dev=True)
    assert msg and "local_dev" in msg
