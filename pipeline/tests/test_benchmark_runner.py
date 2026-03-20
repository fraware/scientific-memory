"""Tests for benchmark regression (min thresholds, runtime budget, ceiling metrics)."""

import json
from pathlib import Path

from sm_pipeline.benchmark_runner import check_regression, run_benchmarks


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


def test_check_regression_llm_suggestions_min_breach(tmp_path: Path) -> None:
    _write_thresholds(
        tmp_path,
        {
            "tasks": {
                "llm_suggestions": {
                    "papers_scanned": 5,
                    "llm_claim_proposal_files": 0,
                }
            },
        },
    )
    report = {
        "tasks": {
            "llm_suggestions": {
                "papers_scanned": 2,
                "llm_claim_proposal_files": 0,
            }
        }
    }
    ok, msg = check_regression(tmp_path, report)
    assert ok is False
    assert "llm_suggestions" in msg
    assert "papers_scanned" in msg


def test_run_benchmarks_includes_llm_suggestions_with_expected_keys() -> None:
    repo = Path(__file__).resolve().parents[2]
    report = run_benchmarks(repo)
    task = report["tasks"].get("llm_suggestions")
    assert isinstance(task, dict)
    assert "error" not in task
    for key in (
        "papers_scanned",
        "llm_claim_proposal_files",
        "canonical_claims_unresolved_assumption_links",
    ):
        assert key in task


def test_run_benchmarks_includes_llm_lean_suggestions_with_expected_keys() -> None:
    repo = Path(__file__).resolve().parents[2]
    report = run_benchmarks(repo)
    task = report["tasks"].get("llm_lean_suggestions")
    assert isinstance(task, dict)
    assert "error" not in task
    for key in (
        "papers_scanned",
        "llm_lean_proposal_files",
        "lean_proposals_conversion_ready",
    ):
        assert key in task


def test_run_benchmarks_includes_llm_eval_with_expected_keys() -> None:
    repo = Path(__file__).resolve().parents[2]
    report = run_benchmarks(repo)
    task = report["tasks"].get("llm_eval")
    assert isinstance(task, dict)
    assert "error" not in task
    for key in (
        "cases_scanned",
        "gold_claim_id_recall_micro",
        "lean_reference_conversion_ready",
    ):
        assert key in task


def test_check_regression_llm_lean_min_breach(tmp_path: Path) -> None:
    _write_thresholds(
        tmp_path,
        {
            "tasks": {
                "llm_lean_suggestions": {
                    "lean_proposals_total": 5,
                }
            },
        },
    )
    report = {
        "tasks": {
            "llm_lean_suggestions": {
                "lean_proposals_total": 1,
            }
        }
    }
    ok, msg = check_regression(tmp_path, report)
    assert ok is False
    assert "llm_lean_suggestions" in msg


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
