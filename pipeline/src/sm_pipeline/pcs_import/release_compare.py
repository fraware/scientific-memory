"""Compare two PCS releases using lineage and claims index (no bundle rescan)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from sm_pipeline.pcs_import.claim_index import query_claims_index
from sm_pipeline.pcs_import.claim_lineage import load_lineage
from sm_pipeline.pcs_import.claim_query import claims_root
from sm_pipeline.pcs_import.lineage_ops import (
    diff_artifact_hashes,
    recommended_action_for_state,
)
from sm_pipeline.pcs_import.stale_check import STALE_REPAIR_HINT, normalize_stale_reason


def _load_json(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    import json

    data = json.loads(path.read_text(encoding="utf-8-sig"))
    return data if isinstance(data, dict) else None


def _diff_workflow_profile(old_dir: Path, new_dir: Path) -> list[dict[str, str]]:
    old_profile = _load_json(old_dir / "workflow_profile.json")
    new_profile = _load_json(new_dir / "workflow_profile.json")
    if old_profile is None and new_profile is None:
        return []
    fields = (
        "workflow_id",
        "domain",
        "description",
        "limitations_notice",
        "signature_or_digest",
    )
    changes: list[dict[str, str]] = []
    for field in fields:
        prev = str((old_profile or {}).get(field) or "")
        cur = str((new_profile or {}).get(field) or "")
        if prev != cur:
            changes.append({"field": field, "previous": prev, "current": cur})
    for label, key in (
        ("runtime_artifacts", "runtime_artifacts"),
        ("certificate_artifacts", "certificate_artifacts"),
    ):
        prev_list = list((old_profile or {}).get(key) or [])
        cur_list = list((new_profile or {}).get(key) or [])
        if prev_list != cur_list:
            changes.append(
                {
                    "field": label,
                    "previous": ",".join(prev_list),
                    "current": ",".join(cur_list),
                },
            )
    return changes


def _diff_registry_checks(old_dir: Path, new_dir: Path) -> list[dict[str, str]]:
    old_validation = _load_json(old_dir / "release_chain_validation.json")
    new_validation = _load_json(new_dir / "release_chain_validation.json")
    if old_validation is None or new_validation is None:
        return []

    def _check_key(check: dict[str, Any]) -> str:
        return str(check.get("check_id") or "")

    def _check_map(validation: dict[str, Any]) -> dict[str, dict[str, Any]]:
        out: dict[str, dict[str, Any]] = {}
        for check in validation.get("checks") or []:
            if isinstance(check, dict):
                key = _check_key(check)
                if key:
                    out[key] = check
        return out

    old_checks = _check_map(old_validation)
    new_checks = _check_map(new_validation)
    changes: list[dict[str, str]] = []
    for check_id in sorted(set(old_checks) | set(new_checks)):
        prev = old_checks.get(check_id, {})
        cur = new_checks.get(check_id, {})
        prev_status = str(prev.get("status") or "")
        cur_status = str(cur.get("status") or "")
        if prev_status != cur_status:
            changes.append(
                {
                    "check_id": check_id,
                    "previous": prev_status,
                    "current": cur_status,
                },
            )
    old_deferred = old_validation.get("deferred_registry_checks") or []
    new_deferred = new_validation.get("deferred_registry_checks") or []
    if old_deferred != new_deferred:
        changes.append(
            {
                "check_id": "deferred_registry_checks",
                "previous": str(len(old_deferred)),
                "current": str(len(new_deferred)),
            },
        )
    return changes


def _entry_for_release(repo_root: Path, release_id: str) -> dict[str, Any] | None:
    matches = query_claims_index(repo_root, release_id=release_id)
    if not matches:
        return None
    return max(matches, key=lambda row: str(row.get("imported_at") or ""))


def _computation_snapshot(lineage: dict[str, Any]) -> dict[str, Any]:
    computation = lineage.get("computation")
    return dict(computation) if isinstance(computation, dict) else {}


def _diff_formal_checks(old_lineage: dict[str, Any], new_lineage: dict[str, Any]) -> list[dict[str, str]]:
    """Diff formal trust kernel lineage fields (ProofObligation / LeanCheckResult)."""
    old_ft = old_lineage.get("formal_trust")
    new_ft = new_lineage.get("formal_trust")
    if not isinstance(old_ft, dict) and not isinstance(new_ft, dict):
        return []
    old_ft = old_ft if isinstance(old_ft, dict) else {}
    new_ft = new_ft if isinstance(new_ft, dict) else {}
    changes: list[dict[str, str]] = []
    for field in (
        "lean_check_status",
        "obligation_set_id",
        "lean_check_result_id",
    ):
        prev = str(old_ft.get(field) or "")
        cur = str(new_ft.get(field) or "")
        if prev != cur:
            changes.append({"field": field, "previous": prev, "current": cur})
    old_theorems = sorted(str(t) for t in (old_ft.get("lean_theorems") or []) if str(t).strip())
    new_theorems = sorted(str(t) for t in (new_ft.get("lean_theorems") or []) if str(t).strip())
    if old_theorems != new_theorems:
        changes.append(
            {
                "field": "lean_theorems",
                "previous": ",".join(old_theorems),
                "current": ",".join(new_theorems),
            },
        )
    old_failed = sorted(str(t) for t in (old_ft.get("failed_lean_theorems") or []) if str(t).strip())
    new_failed = sorted(str(t) for t in (new_ft.get("failed_lean_theorems") or []) if str(t).strip())
    if old_failed != new_failed:
        changes.append(
            {
                "field": "failed_lean_theorems",
                "previous": ",".join(old_failed),
                "current": ",".join(new_failed),
            },
        )
    return changes


def _diff_computation_evidence(
    old_lineage: dict[str, Any],
    new_lineage: dict[str, Any],
) -> dict[str, list[dict[str, str]]]:
    """Diff computation lineage fields (dataset, environment, run, results, witness)."""
    old_c = _computation_snapshot(old_lineage)
    new_c = _computation_snapshot(new_lineage)
    if not old_c and not new_c:
        return {}

    def _changes(field: str) -> list[dict[str, str]]:
        prev = str(old_c.get(field) or "")
        cur = str(new_c.get(field) or "")
        if prev == cur:
            return []
        return [{"field": field, "previous": prev, "current": cur}]

    dataset_changes = _changes("dataset_id") + _changes("dataset_version") + _changes(
        "dataset_aggregate_hash",
    )
    environment_changes = _changes("environment_id")
    code_changes = _changes("code_commit")
    command_changes = _changes("command")

    old_results = list(old_c.get("result_hashes") or [])
    new_results = list(new_c.get("result_hashes") or [])
    result_changes: list[dict[str, str]] = []
    if old_results != new_results:
        result_changes.append(
            {
                "field": "result_hashes",
                "previous": ",".join(old_results),
                "current": ",".join(new_results),
            },
        )
    if old_c.get("result_hash") != new_c.get("result_hash"):
        result_changes.append(
            {
                "field": "result_hash",
                "previous": str(old_c.get("result_hash") or ""),
                "current": str(new_c.get("result_hash") or ""),
            },
        )

    witness_changes = _changes("witness_status") + _changes("witness_id")
    for key in ("dataset_hash", "environment_hash", "run_receipt_hash"):
        witness_changes.extend(_changes(key))

    out: dict[str, list[dict[str, str]]] = {}
    if dataset_changes:
        out["dataset_changes"] = dataset_changes
    if environment_changes:
        out["environment_changes"] = environment_changes
    if code_changes:
        out["code_commit_changes"] = code_changes
    if command_changes:
        out["command_changes"] = command_changes
    if result_changes:
        out["result_hash_changes"] = result_changes
    if witness_changes:
        out["witness_status_changes"] = witness_changes
    return out


def _lineage_hashes(claim_dir: Path) -> dict[str, str]:
    lineage = load_lineage(claim_dir)
    if lineage is None:
        return {}
    hashes = lineage.get("artifact_hashes")
    return dict(hashes) if isinstance(hashes, dict) else {}


def compare_releases(
    repo_root: Path,
    *,
    old_release_id: str,
    new_release_id: str,
) -> dict[str, Any]:
    """Diff two releases via stored lineage records."""
    root = repo_root.resolve()
    old_entry = _entry_for_release(root, old_release_id)
    new_entry = _entry_for_release(root, new_release_id)
    if old_entry is None:
        raise FileNotFoundError(f"no indexed claim for release_id={old_release_id!r}")
    if new_entry is None:
        raise FileNotFoundError(f"no indexed claim for release_id={new_release_id!r}")

    old_claim_id = str(old_entry.get("claim_id") or "")
    new_claim_id = str(new_entry.get("claim_id") or "")
    old_dir = claims_root(root) / str(old_entry.get("claim_dir") or old_claim_id)
    new_dir = claims_root(root) / str(new_entry.get("claim_dir") or new_claim_id)

    old_lineage = load_lineage(old_dir) or {}
    new_lineage = load_lineage(new_dir) or {}

    changed_artifacts, changed_hashes = diff_artifact_hashes(
        _lineage_hashes(new_dir),
        _lineage_hashes(old_dir),
    )

    old_commits = dict(old_lineage.get("source_commits") or {})
    new_commits = dict(new_lineage.get("source_commits") or {})
    changed_source_commits: list[dict[str, str]] = []
    for key in sorted(set(old_commits) | set(new_commits)):
        prev = str(old_commits.get(key) or "")
        cur = str(new_commits.get(key) or "")
        if prev != cur:
            changed_source_commits.append(
                {"component": key, "previous": prev, "current": cur},
            )

    changed_certificates: list[dict[str, str]] = []
    old_cert = str(old_lineage.get("certificate_id") or old_entry.get("certificate_id") or "")
    new_cert = str(new_lineage.get("certificate_id") or new_entry.get("certificate_id") or "")
    if old_cert != new_cert:
        changed_certificates.append(
            {"field": "certificate_id", "previous": old_cert, "current": new_cert},
        )

    old_trace = str(old_lineage.get("trace_hash") or old_entry.get("trace_hash") or "")
    new_trace = str(new_lineage.get("trace_hash") or new_entry.get("trace_hash") or "")
    if old_trace != new_trace:
        changed_certificates.append(
            {"field": "trace_hash", "previous": old_trace, "current": new_trace},
        )

    staleness_impact: list[str] = []
    if str(old_lineage.get("signed_bundle_hash") or "") != str(
        new_lineage.get("signed_bundle_hash") or "",
    ):
        staleness_impact.append(normalize_stale_reason("signed_bundle_hash changed"))
    if str(old_lineage.get("release_manifest_hash") or "") != str(
        new_lineage.get("release_manifest_hash") or "",
    ):
        staleness_impact.append(normalize_stale_reason("release_manifest_hash changed"))
    if old_cert != new_cert:
        staleness_impact.append(normalize_stale_reason("certificate_id changed"))
    if old_trace != new_trace:
        staleness_impact.append(normalize_stale_reason("trace_hash changed"))
    if changed_source_commits:
        staleness_impact.append(normalize_stale_reason("source_commit changed"))
    old_schema = dict(old_lineage.get("schema_versions") or {})
    new_schema = dict(new_lineage.get("schema_versions") or {})
    if old_schema != new_schema:
        staleness_impact.append(normalize_stale_reason("schema_version changed"))

    changed_workflow_profile = _diff_workflow_profile(old_dir, new_dir)
    changed_registry_checks = _diff_registry_checks(old_dir, new_dir)
    changed_formal_checks = _diff_formal_checks(old_lineage, new_lineage)
    changed_computation = _diff_computation_evidence(old_lineage, new_lineage)
    if changed_workflow_profile:
        staleness_impact.append(normalize_stale_reason("workflow_profile changed"))
    if changed_registry_checks:
        staleness_impact.append(normalize_stale_reason("registry_checks changed"))
    if changed_formal_checks:
        staleness_impact.append(normalize_stale_reason("formal_checks changed"))
    if changed_computation:
        for key in changed_computation:
            staleness_impact.append(normalize_stale_reason(f"computation_{key}"))

    recommended = (
        "Import the newer release manifest and refresh lineage."
        if new_entry.get("imported_at", "") >= old_entry.get("imported_at", "")
        else recommended_action_for_state("superseded", stale=False)
    )
    if staleness_impact:
        recommended = STALE_REPAIR_HINT

    return {
        "old_release_id": old_release_id,
        "new_release_id": new_release_id,
        "old_claim_id": old_claim_id,
        "new_claim_id": new_claim_id,
        "changed_artifacts": changed_artifacts,
        "changed_hashes": changed_hashes,
        "changed_source_commits": changed_source_commits,
        "changed_certificates": changed_certificates,
        "changed_workflow_profile": changed_workflow_profile,
        "changed_registry_checks": changed_registry_checks,
        "changed_formal_checks": changed_formal_checks,
        "changed_computation": changed_computation,
        "staleness_impact": sorted(set(staleness_impact)),
        "recommended_action": recommended,
    }
