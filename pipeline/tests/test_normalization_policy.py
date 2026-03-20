"""Tests for normalization policy checks (waiver-backed 8.3)."""

import json
import tempfile
from pathlib import Path

from sm_pipeline.validate.normalization_policy import load_policy, run_policy_checks


def test_load_policy_missing_returns_none() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        assert load_policy(root) is None


def test_load_policy_valid_returns_dict() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        policy_dir = root / "benchmarks"
        policy_dir.mkdir(parents=True)
        policy_dir.joinpath("normalization_policy.json").write_text(
            json.dumps({"duplicate_waivers": ["theta"], "assumption_coverage_max_unlinked": 5}),
            encoding="utf-8",
        )
        p = load_policy(root)
        assert p is not None
        assert p.get("duplicate_waivers") == ["theta"]
        assert p.get("assumption_coverage_max_unlinked") == 5


def test_run_policy_checks_no_policy() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        report = run_policy_checks(root, policy=None)
        assert report["policy_loaded"] is False
        assert "unwaived_duplicates" in report
        assert "warnings" in report


def test_run_policy_checks_with_waivers() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        policy = {"duplicate_waivers": ["theta", "p"], "assumption_coverage_max_unlinked": 100}
        report = run_policy_checks(root, policy=policy)
        assert report["policy_loaded"] is True
        assert report["assumption_coverage_ok"] is True
