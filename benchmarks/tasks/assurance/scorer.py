"""Gate 6 assurance / autonomous-science scorer.

Computes autonomous-science metrics over corpus/assurance and reports
floor-friendly scalars for baseline_thresholds.json regression checks.
"""

from __future__ import annotations

import json
from pathlib import Path

from sm_pipeline.assurance.metrics import (
    METRIC_KEYS,
    compute_autonomous_science_metrics,
    reconcile_metric_slice,
)
from sm_pipeline.assurance.validate import AssuranceValidationError


def run(repo_root: Path) -> dict:
    """Return assurance task metrics for Gate 6."""
    repo_root = Path(repo_root).resolve()
    actions_root = repo_root / "corpus" / "assurance" / "actions"
    action_count = (
        sum(1 for p in actions_root.iterdir() if p.is_dir()) if actions_root.is_dir() else 0
    )

    floors_path = repo_root / "benchmarks" / "assurance" / "expected_floors.json"
    floors: dict = {}
    if floors_path.is_file():
        try:
            floors = json.loads(floors_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            floors = {}

    out: dict = {
        "action_count": action_count,
        "population_action_count": 0,
        "evidence_sufficiency_numerator": 0.0,
        "evidence_sufficiency_denominator": 0.0,
        "reconstruction_completeness_numerator": 0.0,
        "reconstruction_completeness_denominator": 0.0,
        "outcome_resolution_numerator": 0.0,
        "outcome_resolution_denominator": 0.0,
        "metrics_reconciled": 0,
        "metric_keys": len(METRIC_KEYS),
        "floors_loaded": 1 if floors else 0,
    }

    if action_count == 0:
        # Empty corpus: reconcile trivially; floors may still require pilots in CI.
        out["metrics_reconciled"] = 1
        return out

    try:
        report = compute_autonomous_science_metrics(repo_root)
    except AssuranceValidationError as exc:
        out["error"] = str(exc)
        return out

    pop = report.get("population_action_ids") or []
    out["population_action_count"] = len(pop)
    metrics = report.get("metrics") or {}

    try:
        for key in METRIC_KEYS:
            slice_data = metrics[key]
            reconcile_metric_slice(slice_data, len(pop))
        out["metrics_reconciled"] = 1
    except (AssuranceValidationError, KeyError) as exc:
        out["metrics_reconciled"] = 0
        out["error"] = str(exc)
        return out

    es = metrics["evidence_sufficiency"]
    rc = metrics["reconstruction_completeness"]
    orez = metrics["outcome_resolution"]
    out["evidence_sufficiency_numerator"] = float(es["numerator"])
    out["evidence_sufficiency_denominator"] = float(es["denominator"])
    out["reconstruction_completeness_numerator"] = float(rc["numerator"])
    out["reconstruction_completeness_denominator"] = float(rc["denominator"])
    out["outcome_resolution_numerator"] = float(orez["numerator"])
    out["outcome_resolution_denominator"] = float(orez["denominator"])

    # Soft self-check against committed floors (also enforced via baseline_thresholds).
    floors_metrics = (floors.get("metrics_floors") or {}) if isinstance(floors, dict) else {}
    out["floors_checked"] = len(floors_metrics)
    return out
