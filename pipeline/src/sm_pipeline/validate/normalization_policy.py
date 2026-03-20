"""Normalization policy checks (SPEC 8.3): waiver-backed cross-paper duplicates, coverage targets.

Policy file: benchmarks/normalization_policy.json (optional). When absent, no policy enforcement.
Report is machine-readable; checks run in warn-only mode unless promoted to fail via CI/config.
"""

import json
from pathlib import Path

from sm_pipeline.metrics.dimension_visibility import compute_dimension_visibility
from sm_pipeline.metrics.normalization_visibility import compute_normalization_visibility
from sm_pipeline.metrics.symbol_conflict import compute_cross_paper_normalized_duplicates


DEFAULT_POLICY_PATH = "benchmarks/normalization_policy.json"


def load_policy(repo_root: Path) -> dict | None:
    """Load normalization policy from repo. Returns None if file missing or invalid."""
    path = Path(repo_root).resolve() / DEFAULT_POLICY_PATH
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else None
    except (json.JSONDecodeError, OSError):
        return None


def run_policy_checks(repo_root: Path, policy: dict | None = None) -> dict:
    """
    Run normalization visibility + cross-paper duplicates + dimension visibility,
    apply policy (waivers, coverage targets), return machine-readable report.
    """
    repo_root = Path(repo_root).resolve()
    if policy is None:
        policy = load_policy(repo_root)

    report: dict = {
        "policy_loaded": policy is not None,
        "unwaived_duplicates": [],
        "waived_duplicates": [],
        "assumption_coverage_ok": True,
        "assumption_coverage_message": "",
        "kernel_dimension_violations": [],
        "warnings": [],
    }

    dup_result = compute_cross_paper_normalized_duplicates(repo_root)
    duplicate_names = list(dup_result.get("duplicate_names") or [])
    waivers: set[str] = set()
    if policy:
        raw = policy.get("duplicate_waivers")
        if isinstance(raw, list):
            waivers = {str(w) for w in raw}

    for name in duplicate_names:
        if name in waivers:
            report["waived_duplicates"].append(name)
        else:
            report["unwaived_duplicates"].append(name)

    vis_result = compute_normalization_visibility(repo_root)
    unlinked_count = int(vis_result.get("claims_without_linked_assumptions_count") or 0)
    max_unlinked = None
    if policy and "assumption_coverage_max_unlinked" in policy:
        max_unlinked = policy.get("assumption_coverage_max_unlinked")
    if max_unlinked is not None and isinstance(max_unlinked, (int, float)):
        if unlinked_count > int(max_unlinked):
            report["assumption_coverage_ok"] = False
            report["assumption_coverage_message"] = (
                f"claims_without_linked_assumptions_count={unlinked_count} exceeds max {int(max_unlinked)}"
            )
            report["warnings"].append(report["assumption_coverage_message"])

    dim_result = compute_dimension_visibility(repo_root)
    without_count = int(dim_result.get("without_count") or 0)
    max_without = None
    if policy and "max_symbols_without_dimension" in policy:
        max_without = policy.get("max_symbols_without_dimension")
    if max_without is not None and isinstance(max_without, (int, float)):
        if without_count > int(max_without):
            report["kernel_dimension_violations"].append(
                f"symbols_without_dimensional_metadata={without_count} exceeds max {int(max_without)}"
            )
            report["warnings"].append(report["kernel_dimension_violations"][-1])

    if report["unwaived_duplicates"]:
        report["warnings"].append(
            f"Unwaived cross-paper duplicate normalized_name(s): {report['unwaived_duplicates']}"
        )

    return report
