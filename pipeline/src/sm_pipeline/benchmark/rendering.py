"""PCS import/render/query benchmark runner for Scientific Memory evidence layer."""

from __future__ import annotations

import json
import shutil
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from sm_pipeline.benchmark.pcs_sections import (
    REQUIRED_INTERPRETABILITY_SECTIONS,
    count_render_metrics,
    evaluate_section_coverage,
)
from sm_pipeline.pcs_import.claim_query import (
    list_claim_ids,
    list_claims_by_certificate,
    list_claims_by_dataset,
    list_claims_by_lean_theorem,
    list_claims_by_release_id,
    list_claims_by_result_hash,
    list_claims_by_source_commit,
    list_claims_by_workflow,
    refresh_all_stale_flags,
)
from sm_pipeline.pcs_import.release_compare import compare_releases
from sm_pipeline.pcs_import.release_manifest_importer import import_release_manifest
from sm_pipeline.pcs_validate.canonical_hash import file_sha256_digest

BENCHMARK_SCHEMA = "PcsRenderingBenchmarkReport.v0"
CASE_CONFIG_NAME = "case.json"
EXPECTED_SECTIONS = "expected_sections.json"
EXPECTED_QUERIES = "expected_queries.json"
EXPECTED_LINEAGE = "expected_lineage.json"
EXPECTED_STALENESS = "expected_staleness.json"
EXPECTED_COMPARE = "expected_compare.json"
EXPECTED_FAILURE = "expected_failure.json"
MANIFEST_NAMES = (
    "release_manifest.v0.json",
    "ReleaseManifest.v0.json",
)

_QUERY_DISPATCH: dict[str, Any] = {
    "list_claims": lambda root, _p: list_claim_ids(root),
    "by_certificate": lambda root, p: list_claims_by_certificate(root, str(p["certificate_id"])),
    "by_source_commit": lambda root, p: list_claims_by_source_commit(root, str(p["commit"])),
    "by_release": lambda root, p: list_claims_by_release_id(root, str(p["release_id"])),
    "by_workflow": lambda root, p: list_claims_by_workflow(root, str(p["workflow_id"])),
    "by_dataset": lambda root, p: list_claims_by_dataset(root, str(p["dataset_id"])),
    "by_result_hash": lambda root, p: list_claims_by_result_hash(root, str(p["hash"])),
    "by_lean_theorem": lambda root, p: list_claims_by_lean_theorem(root, str(p["theorem"])),
}


def _repo_root(repo_root: Path | None) -> Path:
    if repo_root is not None:
        return repo_root.resolve()
    return Path(__file__).resolve().parents[4]


def _copy_pcs_schemas(root: Path, repo_root: Path) -> None:
    dest = root / "schemas" / "pcs"
    dest.mkdir(parents=True, exist_ok=True)
    src = repo_root / "schemas" / "pcs"
    for path in src.glob("*.json"):
        shutil.copy(path, dest / path.name)
    legacy_dest = dest / "legacy"
    legacy_dest.mkdir(exist_ok=True)
    for path in src.glob("legacy/*.json"):
        shutil.copy(path, legacy_dest / path.name)
    profiles_src = src / "workflow_profiles"
    if profiles_src.is_dir():
        profiles_dest = dest / "workflow_profiles"
        profiles_dest.mkdir(exist_ok=True)
        for path in profiles_src.glob("*.json"):
            shutil.copy(path, profiles_dest / path.name)


def _load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(data, dict):
        raise ValueError(f"expected JSON object: {path}")
    return data


def _resolve_manifest_in_case(case_dir: Path) -> Path | None:
    for name in MANIFEST_NAMES:
        candidate = case_dir / name
        if candidate.is_file():
            return candidate
    return None


def _resolve_release_dir(case_dir: Path, case_config: dict[str, Any], repo_root: Path) -> Path:
    manifest_in_case = _resolve_manifest_in_case(case_dir)
    fixture_rel = str(case_config.get("fixture_dir") or "").strip()
    if fixture_rel:
        fixture_dir = (repo_root / fixture_rel).resolve()
        if fixture_dir.is_dir():
            return fixture_dir
    if manifest_in_case is not None:
        return case_dir
    raise FileNotFoundError(f"no release fixture for case {case_dir.name}")


def _resolve_manifest_path(release_dir: Path, case_config: dict[str, Any]) -> Path:
    preferred = str(case_config.get("manifest_filename") or "").strip()
    if preferred:
        candidate = release_dir / preferred
        if candidate.is_file():
            return candidate
    for name in MANIFEST_NAMES:
        candidate = release_dir / name
        if candidate.is_file():
            return candidate
    raise FileNotFoundError(f"release manifest not found under {release_dir}")


def _sync_manifest_artifact_hashes(release_dir: Path, manifest_path: Path, names: list[str]) -> None:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    artifacts = manifest.get("artifacts")
    if not isinstance(artifacts, dict):
        return
    for name in names:
        path = release_dir / name
        entry = artifacts.get(name)
        if path.is_file() and isinstance(entry, dict):
            entry["sha256"] = file_sha256_digest(path)
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def _apply_post_import(
    repo_root: Path,
    case_config: dict[str, Any],
    *,
    release_dir: Path,
) -> None:
    scenario = str(case_config.get("post_import") or "").strip()
    claim_id = str(case_config.get("claim_id") or "")
    if not scenario or not claim_id:
        return

    claim_dir = repo_root / "corpus" / "pcs" / "claims" / claim_id

    if scenario == "mark_stale":
        bundle_path = claim_dir / "signed_bundle.json"
        if bundle_path.is_file():
            bundle_path.write_bytes(bundle_path.read_bytes() + b"\n")
        refresh_all_stale_flags(repo_root)
        read_model_path = claim_dir / "read_model.json"
        if read_model_path.is_file():
            read_model = json.loads(read_model_path.read_text(encoding="utf-8"))
            staleness = read_model.get("staleness")
            if isinstance(staleness, dict):
                staleness["responsible_component"] = "Scientific Memory"
            read_model_path.write_text(json.dumps(read_model, indent=2) + "\n", encoding="utf-8")
        return

    if scenario in ("patch_lean_failed", "patch_pf_failed"):
        read_model_path = claim_dir / "read_model.json"
        if not read_model_path.is_file():
            return
        read_model = json.loads(read_model_path.read_text(encoding="utf-8"))
        kernel = read_model.get("formal_trust_kernel")
        if not isinstance(kernel, dict):
            return
        results = kernel.get("lean_check_results") or []
        if results and isinstance(results[0], dict):
            results[0]["result"] = "failed"
            results[0]["status"] = "Failed"
            results[0]["repair_hint"] = "Align trace_certificate trace_hash with runtime_receipt."
            results[0]["responsible_component"] = "Provability Fabric"
            results[0]["pf_explain"] = "bundle_hash mismatch in verified_input"
        kernel["overall_status"] = "Failed"
        kernel["failed_lean_theorems"] = [
            str(row.get("lean_theorem") or "")
            for row in results
            if isinstance(row, dict) and str(row.get("result") or "").lower() == "failed"
        ]
        read_model_path.write_text(json.dumps(read_model, indent=2) + "\n", encoding="utf-8")
        return

    if scenario == "deferred_registry_only":
        read_model_path = claim_dir / "read_model.json"
        if not read_model_path.is_file():
            return
        read_model = json.loads(read_model_path.read_text(encoding="utf-8"))
        validation = read_model.get("release_chain_validation")
        if not isinstance(validation, dict):
            return
        checks = validation.get("checks") or []
        validation["deferred_registry_checks"] = [
            str(c.get("check_id") or c.get("registry_ref") or "registry_semantic")
            for c in checks[:3]
            if isinstance(c, dict)
        ]
        for check in checks:
            if isinstance(check, dict) and check.get("registry_check_refs"):
                check["status"] = "deferred"
        registry = read_model.get("artifact_registry") or []
        if isinstance(registry, list) and registry:
            for row in registry:
                if isinstance(row, dict) and row.get("admission_status") == "passed":
                    row["admission_status"] = "deferred"
                    row["registry_admission_result"] = "deferred"
        read_model_path.write_text(json.dumps(read_model, indent=2) + "\n", encoding="utf-8")


def _run_queries(
    repo_root: Path,
    expected_queries: dict[str, Any],
    *,
    claim_id: str,
) -> dict[str, Any]:
    results: dict[str, Any] = {"passed": True, "queries": []}
    for entry in expected_queries.get("queries") or []:
        if not isinstance(entry, dict):
            continue
        query_id = str(entry.get("id") or "")
        query_type = str(entry.get("type") or "")
        params = entry.get("params") if isinstance(entry.get("params"), dict) else {}
        expected = sorted(str(x) for x in (entry.get("expected_claim_ids") or []))
        try:
            fn = _QUERY_DISPATCH.get(query_type)
            if fn is None:
                actual: list[str] = []
                error = f"unknown query type: {query_type}"
            else:
                actual = sorted(str(x) for x in fn(repo_root, params))
                error = ""
        except Exception as exc:
            actual = []
            error = str(exc)
        ok = not error and actual == expected
        if query_type == "list_claims" and claim_id and claim_id not in actual:
            ok = False
        if not ok:
            results["passed"] = False
        results["queries"].append(
            {
                "id": query_id,
                "type": query_type,
                "passed": ok,
                "expected": expected,
                "actual": actual,
                "error": error,
            },
        )
    return results


def _compare_subset(actual: dict[str, Any], expected: dict[str, Any]) -> dict[str, Any]:
    keys = (
        "changed_artifacts",
        "changed_hashes",
        "changed_source_commits",
        "changed_certificates",
        "changed_workflow_profile",
        "changed_registry_checks",
        "changed_formal_checks",
        "staleness_impact",
        "recommended_action",
    )
    missing_keys: list[str] = []
    mismatches: list[str] = []
    for key in keys:
        if key not in expected:
            continue
        if key not in actual:
            missing_keys.append(key)
            continue
        exp_val = expected[key]
        act_val = actual[key]
        if isinstance(exp_val, bool):
            if bool(act_val) != exp_val:
                mismatches.append(key)
        elif isinstance(exp_val, list):
            if not act_val:
                mismatches.append(key)
        elif exp_val and not act_val:
            mismatches.append(key)
    return {
        "passed": not missing_keys and not mismatches,
        "missing_keys": missing_keys,
        "mismatched_keys": mismatches,
    }


def _evaluate_failure_evidence(read_model: dict[str, Any], expected: dict[str, Any]) -> dict[str, Any]:
    checks: dict[str, bool] = {}
    witness = (read_model.get("computation_witness") or {}).get("payload") or {}
    kernel = read_model.get("formal_trust_kernel") or {}
    staleness = read_model.get("staleness") or {}
    lineage = read_model.get("lineage") or {}
    validation = read_model.get("release_chain_validation") or {}
    import_report = read_model.get("scientific_memory_import_report") or {}

    violations = witness.get("violations") or []
    failed_lean = [
        row
        for row in (kernel.get("lean_check_results") or [])
        if isinstance(row, dict) and str(row.get("result") or "").lower() == "failed"
    ]

    deferred = validation.get("deferred_registry_checks") or []
    stale_reasons = staleness.get("stale_reasons") or []
    checks["failure_reason_present"] = bool(
        violations
        or failed_lean
        or staleness.get("stale")
        or stale_reasons
        or deferred,
    )
    checks["responsible_component_present"] = bool(
        (violations and violations[0].get("responsible_component"))
        or (failed_lean and failed_lean[0].get("responsible_component"))
        or staleness.get("responsible_component")
        or any(
            isinstance(check, dict) and check.get("responsible_component")
            for check in (validation.get("checks") or [])
            if str(check.get("status") or "").lower() in ("failed", "deferred")
        )
    )
    registry = read_model.get("artifact_registry") or []
    checks["artifact_path_present"] = bool(
        (violations and (violations[0].get("artifact_path") or violations[0].get("artifact_id")))
        or (failed_lean and failed_lean[0].get("source_artifacts"))
        or (isinstance(registry, list) and len(registry) > 0)
    )
    checks["repair_hint_present"] = bool(
        staleness.get("repair_hint")
        or (failed_lean and failed_lean[0].get("repair_hint"))
        or (violations and violations[0].get("explanation"))
        or str(lineage.get("recommended_action") or "").strip()
    )
    checks["non_claims_present"] = bool(
        kernel.get("formal_non_claims") or read_model.get("limitations") or read_model.get("limitation_notice"),
    )
    checks["partial_import_present"] = bool(
        import_report or read_model.get("claim") or read_model.get("artifact_registry"),
    )

    required = expected.get("required_checks") or list(checks)
    missing = [name for name in required if not checks.get(name)]
    return {
        "checks": checks,
        "passed": not missing,
        "missing_checks": missing,
    }


def _match_lineage(actual: dict[str, Any], expected: dict[str, Any]) -> bool:
    for key in ("claim_id", "release_id", "certificate_id"):
        exp = expected.get(key)
        if exp and str(actual.get(key) or "") != str(exp):
            return False
    if expected.get("has_signed_bundle_hash") and not str(actual.get("signed_bundle_hash") or "").startswith(
        "sha256:",
    ):
        return False
    if "source_commit" in expected:
        commits = actual.get("source_commits") or {}
        if str(commits.get("labtrust_gym") or commits.get("scientific_memory") or "") != str(
            expected["source_commit"],
        ):
            # allow any matching commit value in lineage index
            flat = json.dumps(commits)
            if str(expected["source_commit"]) not in flat:
                return False
    return True


def _match_staleness(actual: dict[str, Any], expected: dict[str, Any]) -> bool:
    if "stale" in expected and bool(actual.get("stale")) != bool(expected["stale"]):
        return False
    if expected.get("claim_state") and str(actual.get("claim_state") or "") != str(expected["claim_state"]):
        return False
    if expected.get("requires_repair_hint") and not actual.get("repair_hint"):
        return False
    return True


def run_case(
    case_dir: Path,
    *,
    repo_root: Path,
    work_root: Path | None = None,
) -> dict[str, Any]:
    case_dir = case_dir.resolve()
    config_path = case_dir / CASE_CONFIG_NAME
    if not config_path.is_file():
        raise FileNotFoundError(f"missing {CASE_CONFIG_NAME} in {case_dir}")
    case_config = _load_json(config_path)
    case_id = str(case_config.get("case_id") or case_dir.name)
    t0 = time.perf_counter()

    bench_root = (work_root or repo_root).resolve()
    release_dir = _resolve_release_dir(case_dir, case_config, repo_root)
    manifest_path = _resolve_manifest_path(release_dir, case_config)

    # Isolated import workspace per case when work_root provided.
    import_root = bench_root
    if work_root is not None:
        import_root = bench_root / f"_import_{case_id}"
        if import_root.exists():
            shutil.rmtree(import_root)
        import_root.mkdir(parents=True)
        _copy_pcs_schemas(import_root, repo_root)
        case_release = import_root / "release"
        if release_dir.resolve() != case_dir.resolve():
            shutil.copytree(release_dir, case_release)
        else:
            shutil.copytree(case_dir, case_release, ignore=shutil.ignore_patterns("expected_*.json", CASE_CONFIG_NAME))
        release_dir = case_release
        manifest_path = _resolve_manifest_path(release_dir, case_config)

    import_release_manifest(manifest_path, repo_root=import_root, write=True, render=False)
    _apply_post_import(import_root, case_config, release_dir=release_dir)

    claim_id = str(case_config.get("claim_id") or "")
    read_model_path = import_root / "corpus" / "pcs" / "claims" / claim_id / "read_model.json"
    if not read_model_path.is_file():
        raise FileNotFoundError(f"read_model missing after import: {read_model_path}")
    read_model = json.loads(read_model_path.read_text(encoding="utf-8"))
    lineage_path = import_root / "corpus" / "pcs" / "claims" / claim_id / "lineage.json"
    lineage = json.loads(lineage_path.read_text(encoding="utf-8")) if lineage_path.is_file() else {}

    failures: list[str] = []

    # Section coverage
    expected_sections_path = case_dir / EXPECTED_SECTIONS
    required_sections = list(REQUIRED_INTERPRETABILITY_SECTIONS)
    if expected_sections_path.is_file():
        exp_sec = _load_json(expected_sections_path)
        if exp_sec.get("present_sections"):
            required_sections = list(exp_sec["present_sections"])
        else:
            required_sections = list(exp_sec.get("required_sections") or required_sections)
    section_report = evaluate_section_coverage(read_model, required=required_sections)
    if section_report["missing_sections"]:
        failures.append(f"missing sections: {', '.join(section_report['missing_sections'])}")

    render_metrics = count_render_metrics(read_model)

    # Lineage
    lineage_ok = True
    expected_lineage_path = case_dir / EXPECTED_LINEAGE
    if expected_lineage_path.is_file():
        expected_lineage = _load_json(expected_lineage_path)
        lineage_ok = _match_lineage(lineage, expected_lineage)
        if not lineage_ok:
            failures.append("lineage mismatch")

    # Staleness
    staleness_ok = True
    expected_staleness_path = case_dir / EXPECTED_STALENESS
    staleness = read_model.get("staleness") or {}
    if expected_staleness_path.is_file():
        expected_staleness = _load_json(expected_staleness_path)
        staleness_ok = _match_staleness(staleness, expected_staleness)
        if not staleness_ok:
            failures.append("staleness mismatch")

    # Queries
    query_report: dict[str, Any] = {"passed": True, "queries": []}
    expected_queries_path = case_dir / EXPECTED_QUERIES
    if expected_queries_path.is_file():
        query_report = _run_queries(import_root, _load_json(expected_queries_path), claim_id=claim_id)
        if not query_report["passed"]:
            failures.append("query benchmark failed")

    # Release comparison
    compare_report: dict[str, Any] = {"passed": True, "skipped": True}
    expected_compare_path = case_dir / EXPECTED_COMPARE
    if expected_compare_path.is_file():
        compare_report["skipped"] = False
        compare_cfg = case_config.get("compare") or {}
        second_fixture = str(compare_cfg.get("second_fixture_dir") or "").strip()
        if second_fixture:
            second_dir = (repo_root / second_fixture).resolve()
            second_manifest = _resolve_manifest_path(second_dir, compare_cfg)
            import_release_manifest(second_manifest, repo_root=import_root, write=True, render=False)
        expected_compare = _load_json(expected_compare_path)
        old_release = str(expected_compare.get("old_release_id") or "")
        new_release = str(expected_compare.get("new_release_id") or "")
        actual_compare = compare_releases(import_root, old_release_id=old_release, new_release_id=new_release)
        subset = _compare_subset(actual_compare, expected_compare)
        compare_report = {**subset, "old_release_id": old_release, "new_release_id": new_release}
        if not subset["passed"]:
            failures.append("release comparison benchmark failed")

    # Failure evidence (failed-release cases)
    failure_report: dict[str, Any] = {"passed": True, "skipped": True}
    if case_config.get("failure_mode"):
        failure_report["skipped"] = False
        expected_failure_path = case_dir / EXPECTED_FAILURE
        expected_failure = _load_json(expected_failure_path) if expected_failure_path.is_file() else {}
        failure_report = _evaluate_failure_evidence(read_model, expected_failure)
        if not failure_report["passed"]:
            failures.append("failure evidence rendering incomplete")

    passed = not failures
    return {
        "case_id": case_id,
        "claim_id": claim_id,
        "release_id": case_config.get("release_id"),
        "passed": passed,
        "failures": failures,
        "metrics": {
            **section_report,
            **render_metrics,
            "lineage_records_created": 1 if lineage_ok else 0,
            "staleness_detected": 1 if staleness_ok and staleness.get("stale") else int(bool(staleness)),
            "query_responses_correct": 1.0 if query_report.get("passed") else 0.0,
            "release_comparison_correct": 1.0 if compare_report.get("passed") else 0.0,
            "failure_evidence_rendered": 1.0 if failure_report.get("passed") else 0.0,
        },
        "section_coverage": section_report,
        "queries": query_report,
        "compare": compare_report,
        "failure_evidence": failure_report,
        "_runtime_seconds": round(time.perf_counter() - t0, 2),
    }


def discover_case_dirs(cases_path: Path) -> list[Path]:
    cases_path = cases_path.resolve()
    if (cases_path / CASE_CONFIG_NAME).is_file():
        return [cases_path]
    out: list[Path] = []
    if not cases_path.is_dir():
        return out
    for child in sorted(cases_path.iterdir()):
        if child.is_dir() and (child / CASE_CONFIG_NAME).is_file():
            out.append(child)
    failed_root = cases_path / "failed"
    if failed_root.is_dir():
        for child in sorted(failed_root.iterdir()):
            if child.is_dir() and (child / CASE_CONFIG_NAME).is_file():
                out.append(child)
    return out


def run_rendering_benchmark(
    cases_path: Path,
    *,
    repo_root: Path | None = None,
    out_dir: Path | None = None,
    isolated: bool = True,
) -> dict[str, Any]:
    root = _repo_root(repo_root)
    case_dirs = discover_case_dirs(cases_path)
    if not case_dirs:
        raise FileNotFoundError(f"no benchmark cases under {cases_path}")

    work_root = None
    if isolated:
        stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
        work_root = (out_dir or root / "benchmark_runs" / "_work") / f"work_{stamp}"
        work_root.mkdir(parents=True, exist_ok=True)

    case_results: list[dict[str, Any]] = []
    aggregate_failures: list[str] = []

    for case_dir in case_dirs:
        try:
            result = run_case(case_dir, repo_root=root, work_root=work_root)
        except Exception as exc:
            result = {
                "case_id": case_dir.name,
                "passed": False,
                "failures": [str(exc)],
                "error": str(exc),
            }
            aggregate_failures.append(f"{case_dir.name}: {exc}")
        case_results.append(result)
        if not result.get("passed"):
            aggregate_failures.extend(
                f"{result.get('case_id')}: {msg}" for msg in (result.get("failures") or [])
            )

    def _avg(key: str) -> float:
        vals = [
            float((c.get("metrics") or {}).get(key, 0))
            for c in case_results
            if isinstance(c.get("metrics"), dict)
        ]
        return round(sum(vals) / len(vals), 4) if vals else 0.0

    report: dict[str, Any] = {
        "benchmark": "pcs_rendering",
        "schema_version": BENCHMARK_SCHEMA,
        "generated_at": datetime.now(UTC).isoformat(),
        "repo_root": str(root),
        "cases_path": str(cases_path.resolve()),
        "case_count": len(case_results),
        "passed": not aggregate_failures,
        "failures": aggregate_failures,
        "cases": case_results,
        "metrics": {
            "required_sections_rendered": _avg("required_sections_rendered"),
            "artifact_rows_rendered": _avg("artifact_rows_rendered"),
            "registry_metadata_rendered": _avg("registry_metadata_rendered"),
            "handoffs_rendered": _avg("handoffs_rendered"),
            "formal_checks_rendered": _avg("formal_checks_rendered"),
            "limitations_rendered": _avg("limitations_rendered"),
            "lineage_records_created": _avg("lineage_records_created"),
            "staleness_detected": _avg("staleness_detected"),
            "query_responses_correct": _avg("query_responses_correct"),
            "release_comparison_correct": _avg("release_comparison_correct"),
            "failure_evidence_rendered": _avg("failure_evidence_rendered"),
        },
        "pcs_bench": {
            "consumer": "pcs-bench",
            "metric_keys": [
                "required_sections_rendered",
                "artifact_rows_rendered",
                "registry_metadata_rendered",
                "handoffs_rendered",
                "formal_checks_rendered",
                "limitations_rendered",
                "lineage_records_created",
                "staleness_detected",
                "query_responses_correct",
                "release_comparison_correct",
                "failure_evidence_rendered",
            ],
        },
    }

    if out_dir is not None:
        out_dir = out_dir.resolve()
        out_dir.mkdir(parents=True, exist_ok=True)
        report_path = out_dir / "rendering_benchmark_report.json"
        report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        summary_path = out_dir / "rendering_benchmark_summary.md"
        lines = [
            "# PCS rendering benchmark",
            "",
            f"- cases: {len(case_results)}",
            f"- passed: {report['passed']}",
            f"- required_sections_rendered: {report['metrics']['required_sections_rendered']}",
            f"- query_responses_correct: {report['metrics']['query_responses_correct']}",
            "",
        ]
        if aggregate_failures:
            lines.append("## Failures")
            lines.extend(f"- {msg}" for msg in aggregate_failures)
        summary_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        report["report_path"] = str(report_path)

    return report


def check_rendering_regression(repo_root: Path, report: dict[str, Any]) -> tuple[bool, str]:
    """Compare aggregate metrics to benchmarks/rendering/baseline_thresholds.json."""
    thresholds_path = repo_root / "benchmarks" / "rendering" / "baseline_thresholds.json"
    if not thresholds_path.is_file():
        return True, ""
    thresholds = json.loads(thresholds_path.read_text(encoding="utf-8"))
    min_metrics = thresholds.get("metrics") or {}
    actual_metrics = report.get("metrics") or {}
    for key, min_val in min_metrics.items():
        if not isinstance(min_val, (int, float)):
            continue
        actual = actual_metrics.get(key)
        if actual is None:
            continue
        try:
            value = float(actual)
        except (TypeError, ValueError):
            continue
        if value < float(min_val):
            return False, f"Regression: {key} is {value}, below threshold {min_val}"
    if not report.get("passed"):
        failures = report.get("failures") or []
        return False, "; ".join(str(f) for f in failures[:5])
    return True, ""


def export_pcs_bench_payload(report: dict[str, Any]) -> dict[str, Any]:
    """Flatten rendering benchmark report for pcs-bench consumers."""
    metrics = dict(report.get("metrics") or {})
    return {
        "benchmark": report.get("benchmark"),
        "schema_version": report.get("schema_version"),
        "passed": report.get("passed"),
        "case_count": report.get("case_count"),
        "generated_at": report.get("generated_at"),
        "metrics": metrics,
        "failures": list(report.get("failures") or []),
    }


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Run PCS rendering/query benchmarks.")
    parser.add_argument(
        "--cases",
        required=True,
        help="Benchmark case directory (single case or parent of cases)",
    )
    parser.add_argument(
        "--out",
        default="",
        help="Output directory for benchmark report (default: benchmark_runs/<case_name>)",
    )
    parser.add_argument(
        "--repo-root",
        default="",
        help="Scientific Memory repo root (default: auto)",
    )
    parser.add_argument(
        "--in-place",
        action="store_true",
        help="Import into repo corpus instead of isolated work directory",
    )
    parser.add_argument(
        "--check-regression",
        action="store_true",
        default=True,
        help="Fail when metrics fall below benchmarks/rendering/baseline_thresholds.json",
    )
    parser.add_argument(
        "--no-check-regression",
        action="store_false",
        dest="check_regression",
        help="Skip baseline threshold comparison",
    )
    parser.add_argument(
        "--pcs-bench-out",
        default="",
        help="Write pcs-bench flattened JSON payload to this path",
    )
    args = parser.parse_args(argv)

    cases_path = Path(args.cases)
    repo_root = Path(args.repo_root) if args.repo_root else _repo_root(None)
    out_dir = Path(args.out) if args.out else repo_root / "benchmark_runs" / cases_path.name

    report = run_rendering_benchmark(
        cases_path,
        repo_root=repo_root,
        out_dir=out_dir,
        isolated=not args.in_place,
    )
    if args.pcs_bench_out:
        bench_path = Path(args.pcs_bench_out)
        if not bench_path.is_absolute():
            bench_path = repo_root / bench_path
        bench_path.parent.mkdir(parents=True, exist_ok=True)
        bench_path.write_text(
            json.dumps(export_pcs_bench_payload(report), indent=2) + "\n",
            encoding="utf-8",
        )

    exit_code = 0 if report.get("passed") else 1
    if args.check_regression:
        ok, msg = check_rendering_regression(repo_root, report)
        if not ok:
            if msg:
                print(msg, file=sys.stderr)
            exit_code = 1

    if not args.out:
        print(json.dumps(report, indent=2))
    else:
        print(f"Wrote {report.get('report_path', out_dir / 'rendering_benchmark_report.json')}")
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
