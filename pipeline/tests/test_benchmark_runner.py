"""Tests for benchmark regression (min thresholds, runtime budget, ceiling metrics)."""

import json
from pathlib import Path

from sm_pipeline.benchmark_runner import check_regression


def _write_thresholds(root: Path, data: dict) -> None:
    b = root / "benchmarks"
    b.mkdir(parents=True)
    (b / "baseline_thresholds.json").write_text(json.dumps(data), encoding="utf-8")


def test_check_regression_no_baseline_file_passes(tmp_path: Path) -> None:
    ok, msg = check_regression(tmp_path, {"tasks": {"extraction": {"claim_count": 0}}})
    assert ok is True
    assert msg == ""


def test_check_regression_min_threshold_passes(tmp_path: Path) -> None:
    _write_thresholds(
        tmp_path,
        {"tasks": {"extraction": {"claim_count": 5}}, "tasks_ceiling": {}},
    )
    report = {"tasks": {"extraction": {"claim_count": 10}}}
    ok, msg = check_regression(tmp_path, report)
    assert ok is True
    assert msg == ""


def test_check_regression_min_threshold_fails(tmp_path: Path) -> None:
    _write_thresholds(
        tmp_path,
        {"tasks": {"extraction": {"claim_count": 10}}},
    )
    report = {"tasks": {"extraction": {"claim_count": 5}}}
    ok, msg = check_regression(tmp_path, report)
    assert ok is False
    assert "Regression" in msg
    assert "claim_count" in msg


def test_check_regression_missing_task_fails(tmp_path: Path) -> None:
    _write_thresholds(
        tmp_path,
        {"tasks": {"extraction": {"claim_count": 1}}},
    )
    report = {"tasks": {}}
    ok, msg = check_regression(tmp_path, report)
    assert ok is False
    assert "missing" in msg.lower()


def test_check_regression_runtime_budget(tmp_path: Path) -> None:
    _write_thresholds(
        tmp_path,
        {
            "runtime_budget_seconds_per_task": 1.0,
            "tasks": {},
        },
    )
    report = {"tasks": {"extraction": {"_runtime_seconds": 5.0}}}
    ok, msg = check_regression(tmp_path, report)
    assert ok is False
    assert "Runtime" in msg


def test_check_regression_ceiling_passes(tmp_path: Path) -> None:
    _write_thresholds(
        tmp_path,
        {
            "tasks": {},
            "tasks_ceiling": {"gold": {"source_span_alignment_error_rate": 0.05}},
        },
    )
    report = {"tasks": {"gold": {"source_span_alignment_error_rate": 0.01}}}
    ok, msg = check_regression(tmp_path, report)
    assert ok is True


def test_check_regression_ceiling_fails(tmp_path: Path) -> None:
    _write_thresholds(
        tmp_path,
        {
            "tasks": {},
            "tasks_ceiling": {"gold": {"source_span_alignment_error_rate": 0}},
        },
    )
    report = {"tasks": {"gold": {"source_span_alignment_error_rate": 0.1}}}
    ok, msg = check_regression(tmp_path, report)
    assert ok is False
    assert "Ceiling" in msg


def test_check_regression_ceiling_skips_none(tmp_path: Path) -> None:
    _write_thresholds(
        tmp_path,
        {
            "tasks": {},
            "tasks_ceiling": {"gold": {"source_span_alignment_error_rate": 0}},
        },
    )
    report = {"tasks": {"gold": {}}}
    ok, msg = check_regression(tmp_path, report)
    assert ok is True
