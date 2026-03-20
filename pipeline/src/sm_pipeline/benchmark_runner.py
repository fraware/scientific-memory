"""Run benchmark tasks and emit a report. Uses scorers from repo benchmarks/tasks."""

import importlib.util
import json
import sys
import time
from datetime import UTC, datetime
from pathlib import Path


TASK_NAMES = ("extraction", "mapping", "theorem_cards", "gold")
TREND_HISTORY_MAX_ENTRIES = 100
TREND_HISTORY_FILENAME = "proof_success_history.json"


def run_benchmarks(repo_root: Path) -> dict:
    """Run all task scorers and return a combined report (includes _runtime_seconds per task)."""
    repo_root = repo_root.resolve()
    benchmarks_dir = repo_root / "benchmarks" / "tasks"
    report: dict = {"tasks": {}, "repo_root": str(repo_root)}

    for name in TASK_NAMES:
        scorer_path = benchmarks_dir / name / "scorer.py"
        if not scorer_path.is_file():
            report["tasks"][name] = {"error": "scorer not found"}
            continue
        t0 = time.perf_counter()
        try:
            spec = importlib.util.spec_from_file_location(
                f"benchmarks.tasks.{name}.scorer", scorer_path
            )
            if spec is None or spec.loader is None:
                report["tasks"][name] = {"error": "failed to load module"}
                continue
            mod = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = mod
            spec.loader.exec_module(mod)
            if not hasattr(mod, "run"):
                report["tasks"][name] = {"error": "no run() function"}
                continue
            result = mod.run(repo_root)
            task_result = result if isinstance(result, dict) else {"raw": str(result)}
            task_result["_runtime_seconds"] = round(time.perf_counter() - t0, 2)
            report["tasks"][name] = task_result
        except Exception as e:
            report["tasks"][name] = {"error": str(e), "_runtime_seconds": round(time.perf_counter() - t0, 2)}

    return report


def check_regression(repo_root: Path, report: dict) -> tuple[bool, str]:
    """
    Compare report to baseline_thresholds.json. Return (True, '') if all metrics >= thresholds
    and no task exceeds runtime_budget_seconds_per_task. Return (False, message) otherwise.
    """
    thresholds_path = repo_root / "benchmarks" / "baseline_thresholds.json"
    if not thresholds_path.is_file():
        return True, ""
    thresholds = json.loads(thresholds_path.read_text(encoding="utf-8"))
    task_thresholds = thresholds.get("tasks") or {}
    report_tasks = report.get("tasks") or {}
    budget = thresholds.get("runtime_budget_seconds_per_task")
    if isinstance(budget, (int, float)) and budget > 0:
        for task_name, actual in report_tasks.items():
            if not isinstance(actual, dict):
                continue
            rt = actual.get("_runtime_seconds")
            if rt is not None and float(rt) > float(budget):
                return False, (
                    f"Runtime: {task_name} took {rt}s, above budget {budget}s"
                )
    for task_name, min_vals in task_thresholds.items():
        if not isinstance(min_vals, dict):
            continue
        actual = report_tasks.get(task_name)
        if not isinstance(actual, dict):
            return False, f"Task {task_name}: missing in report"
        for key, min_val in min_vals.items():
            if key.startswith("_"):
                continue
            if not isinstance(min_val, (int, float)):
                continue
            val = actual.get(key)
            if val is None:
                continue
            try:
                v = float(val) if isinstance(val, (int, float)) else float(val)
            except (TypeError, ValueError):
                continue
            if v < min_val:
                return False, (f"Regression: {task_name}.{key} is {v}, below threshold {min_val}")
    ceiling_tasks = thresholds.get("tasks_ceiling") or {}
    if isinstance(ceiling_tasks, dict):
        for task_name, max_vals in ceiling_tasks.items():
            if not isinstance(max_vals, dict):
                continue
            actual = report_tasks.get(task_name)
            if not isinstance(actual, dict):
                continue
            for key, max_val in max_vals.items():
                if str(key).startswith("_"):
                    continue
                if not isinstance(max_val, (int, float)):
                    continue
                raw = actual.get(key)
                if raw is None:
                    continue
                try:
                    v = float(raw)
                except (TypeError, ValueError):
                    continue
                if v > float(max_val):
                    return False, (
                        f"Ceiling breach: {task_name}.{key} is {v}, above max {max_val}"
                    )
    return True, ""


def _proof_success_snapshot(report: dict) -> dict:
    """Derive proof-success trend snapshot from theorem_cards task for CI/reporting."""
    tc = report.get("tasks") or {}
    task = tc.get("theorem_cards")
    if not isinstance(task, dict) or "error" in task:
        return {"machine_checked_count": 0, "declaration_count": 0, "fraction_machine_checked": 0.0}
    decl = int(task.get("declaration_count") or 0)
    mc = int(task.get("machine_checked_count") or 0)
    frac = (mc / decl) if decl else 0.0
    return {
        "machine_checked_count": mc,
        "declaration_count": decl,
        "fraction_machine_checked": round(frac, 4),
    }


def _trend_history_path(report_path: Path) -> Path:
    """Path to proof-success trend history file (under reports/trend/)."""
    base = report_path.parent if report_path else Path("benchmarks/reports")
    return base / "trend" / TREND_HISTORY_FILENAME


def _append_proof_success_trend(report_path: Path, snapshot: dict) -> None:
    """Append current proof_success snapshot to trend history; cap at TREND_HISTORY_MAX_ENTRIES."""
    path = _trend_history_path(report_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            history = data if isinstance(data, list) else []
        except (json.JSONDecodeError, OSError):
            history = []
    else:
        history = []
    entry = {
        "timestamp": datetime.now(UTC).isoformat(),
        "machine_checked_count": snapshot.get("machine_checked_count", 0),
        "declaration_count": snapshot.get("declaration_count", 0),
        "fraction_machine_checked": snapshot.get("fraction_machine_checked", 0.0),
    }
    history.append(entry)
    if len(history) > TREND_HISTORY_MAX_ENTRIES:
        history = history[-TREND_HISTORY_MAX_ENTRIES:]
    path.write_text(json.dumps(history, indent=2), encoding="utf-8")


def _check_proof_success_trend(snapshot: dict, report_path: Path) -> str | None:
    """
    Compare current snapshot to previous run in trend history. Return warning message if
    fraction_machine_checked dropped (Gate 6 trend check, warn-only).
    """
    path = _trend_history_path(report_path)
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        history = data if isinstance(data, list) else []
    except (json.JSONDecodeError, OSError):
        return None
    if len(history) < 2:
        return None
    prev = history[-2]
    curr_frac = float(snapshot.get("fraction_machine_checked") or 0)
    prev_frac = float(prev.get("fraction_machine_checked") or 0)
    if curr_frac < prev_frac:
        return (
            f"Gate 6 trend warning: fraction_machine_checked decreased from {prev_frac} to {curr_frac}. "
            "See reports/trend/proof_success_history.json."
        )
    return None


def main(repo_root: Path, report_path: Path | None = None) -> dict:
    """Run benchmarks and optionally write report JSON. Returns the report dict."""
    report = run_benchmarks(repo_root)
    report["proof_success_snapshot"] = _proof_success_snapshot(report)
    if report_path:
        report_path = Path(report_path)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
        snap = report.get("proof_success_snapshot") or {}
        _append_proof_success_trend(report_path, snap)
        trend_warn = _check_proof_success_trend(snap, report_path)
        summary_path = report_path.parent / "proof_success_summary.md"
        trend_path = _trend_history_path(report_path)
        summary_lines = [
            "# Proof success (Gate 6)",
            "",
            f"- machine_checked: {snap.get('machine_checked_count', 0)}",
            f"- declarations: {snap.get('declaration_count', 0)}",
            f"- fraction_machine_checked: {snap.get('fraction_machine_checked', 0)}",
            "",
            f"Trend history: `{trend_path.name}` (under `reports/trend/`).",
        ]
        if trend_warn:
            summary_lines.extend(["", "**Trend warning:**", trend_warn])
        summary_path.write_text("\n".join(summary_lines), encoding="utf-8")
    else:
        print(json.dumps(report, indent=2))
    return report
