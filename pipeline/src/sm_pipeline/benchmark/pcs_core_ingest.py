"""Project Scientific Memory rendering benchmark outputs to pcs-core v0 artifacts."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from sm_pipeline.benchmark.failure_taxonomy import FAILURE_KINDS
from sm_pipeline.benchmark.pcs_core_coverage import SOURCE_REPO
from sm_pipeline.pcs_validate.canonical_hash import canonical_hash

PCS_WORKFLOW_ID = "pcs.scientific_memory"
UNKNOWN_COMMIT = "0" * 40
EXPLAIN_QUALITY_SIDECARS_DIR = "explain_quality_reports"
COVERAGE_SIDECARS_DIR = "coverage_reports"
BENCHMARK_RUN_SIDECARS_DIR = "benchmark_runs"
FAILURE_LOCALIZATION_SIDECARS_DIR = "failure_localization_reports"

# Top-level SM dialect reports written beside ingest (provenance sidecars).
SM_V0_DIALECT_REPORTS: tuple[str, ...] = (
    "benchmark_run.v0.json",
    "rendering_coverage_report.v0.json",
    "query_coverage_report.v0.json",
    "failed_release_rendering_report.v0.json",
    "explain_quality_report.v0.json",
)

RESPONSIBLE_COMPONENT_ALIASES: dict[str, str] = {
    "scientific memory": "scientific_memory",
    "scientific_memory": "scientific_memory",
    "Scientific Memory": "scientific_memory",
    "Formal Trust Kernel": "formal_kernel",
    "formal trust kernel": "formal_kernel",
    "Provability Fabric": "provability_fabric",
    "LabTrust": "runtime",
    "runtime_producer": "runtime",
    "certificate_producer": "certificate",
    "verifier": "verifier",
    "registry": "registry",
    "unknown": "unknown",
}

SM_COVERAGE_METRICS: tuple[str, ...] = (
    "scientific_memory_interpretability",
    "query_correctness",
    "failed_release_rendering",
    "release_comparison",
    "staleness_detection",
)

# Release-grade producer gate: minimum coverage_ratio per SM metric (details.sm_metric).
RELEASE_GRADE_COVERAGE_THRESHOLDS: dict[str, float] = {
    "scientific_memory_interpretability": 0.95,
    "query_correctness": 0.95,
    "failed_release_rendering": 0.90,
    "release_comparison": 0.90,
    "staleness_detection": 0.90,
}


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _with_digest(doc: dict[str, Any]) -> dict[str, Any]:
    body = dict(doc)
    body["signature_or_digest"] = canonical_hash(body)
    return body


def normalize_source_commit(raw: str) -> str:
    text = (raw or "").strip().lower()
    if len(text) == 40 and all(ch in "0123456789abcdef" for ch in text):
        return text
    return UNKNOWN_COMMIT


def is_zero_source_commit(commit: str) -> bool:
    """True when commit is the all-zero developer fixture placeholder."""
    return normalize_source_commit(commit) == UNKNOWN_COMMIT


def validate_release_grade_source_commit(commit: str) -> list[str]:
    """Reject all-zero commits for release-grade benchmark output."""
    normalized = normalize_source_commit(commit)
    if is_zero_source_commit(normalized):
        return [
            "release-grade: source_commit must be a real 40-char git commit "
            f"(got {normalized!r}); resolve git HEAD or set SCIENTIFIC_MEMORY_REPO_ROOT",
        ]
    return []


def validate_release_grade_coverage_adequacy(coverage_reports: list[Any]) -> list[str]:
    """Enforce minimum coverage_ratio per SM metric for release-grade output."""
    errors: list[str] = []
    projected_metrics: set[str] = set()
    measured_ratios: dict[str, float] = {}
    for index, row in enumerate(coverage_reports):
        if not isinstance(row, dict):
            continue
        details = row.get("details") if isinstance(row.get("details"), dict) else {}
        sm_metric = str(details.get("sm_metric") or "")
        if not sm_metric:
            continue
        projected_metrics.add(sm_metric)
        if details.get("applicability") == "not_applicable" or details.get("case_count") == 0:
            continue
        try:
            ratio = float(row.get("coverage_ratio", 0.0))
        except (TypeError, ValueError):
            errors.append(f"coverage_reports[{index}]: invalid coverage_ratio")
            continue
        measured_ratios[sm_metric] = ratio

    missing_metrics = set(RELEASE_GRADE_COVERAGE_THRESHOLDS) - projected_metrics
    if missing_metrics:
        errors.append(
            "release-grade: missing coverage reports for sm_metric: "
            + ", ".join(sorted(missing_metrics)),
        )

    for sm_metric, minimum in RELEASE_GRADE_COVERAGE_THRESHOLDS.items():
        ratio = measured_ratios.get(sm_metric)
        if ratio is None:
            continue
        if ratio < minimum:
            errors.append(
                f"release-grade: {sm_metric} coverage_ratio {ratio:.4f} "
                f"below threshold {minimum:.2f}",
            )
    return errors


def validate_release_grade_pcs_core_adequacy(ingest: dict[str, Any]) -> list[str]:
    """When pcs_core is installed, require release-grade or external-review-grade adequacy tier."""
    try:
        from pcs_core.benchmark_ingest import assess_ingest_adequacy_tier
    except ImportError:
        return []
    tier, findings = assess_ingest_adequacy_tier(ingest)
    if tier in ("release-grade", "external-review-grade"):
        return []
    detail = "; ".join(findings) if findings else "no findings"
    return [f"release-grade: pcs-core adequacy tier {tier!r} ({detail})"]


def validate_release_grade_ingest(
    ingest: dict[str, Any],
    *,
    out_dir: Path | None = None,
) -> list[str]:
    """Structural + adequacy checks for release-grade PcsBenchIngest.v0 producer output."""
    errors: list[str] = []
    errors.extend(validate_release_grade_source_commit(str(ingest.get("source_commit") or "")))
    runs = ingest.get("benchmark_runs")
    if not isinstance(runs, list) or not runs:
        errors.append("release-grade: benchmark_runs must be non-empty")
    commands = ingest.get("commands")
    if not isinstance(commands, list) or not commands:
        errors.append("release-grade: commands must be non-empty")
    logs = ingest.get("logs")
    if not isinstance(logs, list) or not logs:
        errors.append("release-grade: logs must be non-empty")
    explain = ingest.get("explain_quality_reports")
    if not isinstance(explain, list) or not explain:
        errors.append("release-grade: explain_quality_reports must be non-empty")
    errors.extend(validate_embedded_ingest_contract(ingest, out_dir=out_dir))
    errors.extend(validate_release_grade_pcs_core_adequacy(ingest))
    coverage = ingest.get("coverage_reports")
    if isinstance(coverage, list):
        errors.extend(validate_release_grade_coverage_adequacy(coverage))
    else:
        errors.append("release-grade: coverage_reports must be a list")
    if out_dir is not None:
        errors.extend(validate_release_grade_dialect_artifacts(out_dir))
    for array_key in (
        "benchmark_runs",
        "coverage_reports",
        "failure_localization_reports",
        "explain_quality_reports",
    ):
        rows = ingest.get(array_key)
        if not isinstance(rows, list):
            continue
        for index, row in enumerate(rows):
            if not isinstance(row, dict):
                continue
            nested_commit = row.get("source_commit")
            if nested_commit is not None and is_zero_source_commit(str(nested_commit)):
                errors.append(
                    f"release-grade: {array_key}[{index}].source_commit must not be all zeros",
                )
    return errors


def validate_release_grade_dialect_artifacts(out_dir: Path) -> list[str]:
    """Release-grade: require on-disk SM dialect reports and ingest sidecar directories."""
    errors: list[str] = []
    for filename in SM_V0_DIALECT_REPORTS:
        if not (out_dir / filename).is_file():
            errors.append(f"release-grade: missing dialect artifact {filename}")
    ingest_path = out_dir / "pcs_bench_ingest.v0.json"
    if not ingest_path.is_file():
        errors.append("release-grade: missing pcs_bench_ingest.v0.json")
        return errors
    try:
        ingest = json.loads(ingest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"release-grade: {ingest_path.name}: {exc}"]
    if not isinstance(ingest, dict):
        return ["release-grade: pcs_bench_ingest.v0.json must be an object"]
    if not (out_dir / EXPLAIN_QUALITY_SIDECARS_DIR).is_dir():
        errors.append(f"release-grade: missing {EXPLAIN_QUALITY_SIDECARS_DIR}/")
    if not (out_dir / COVERAGE_SIDECARS_DIR).is_dir():
        errors.append(f"release-grade: missing {COVERAGE_SIDECARS_DIR}/")
    explain_rows = ingest.get("explain_quality_reports")
    if isinstance(explain_rows, list) and explain_rows:
        for index, row in enumerate(explain_rows):
            if not isinstance(row, dict):
                continue
            report_id = str(row.get("report_id") or row.get("case_id") or "case")
            rel = explain_quality_sidecar_relpath(report_id)
            if not (out_dir / rel).is_file():
                errors.append(f"release-grade: missing explain-quality sidecar {rel}")
    fl_rows = ingest.get("failure_localization_reports")
    if isinstance(fl_rows, list) and fl_rows:
        if not (out_dir / FAILURE_LOCALIZATION_SIDECARS_DIR).is_dir():
            errors.append(f"release-grade: missing {FAILURE_LOCALIZATION_SIDECARS_DIR}/")
        for index, row in enumerate(fl_rows):
            if not isinstance(row, dict):
                continue
            result_id = str(row.get("result_id") or row.get("case_id") or "failure-loc")
            rel = failure_localization_sidecar_relpath(result_id)
            if not (out_dir / rel).is_file():
                errors.append(f"release-grade: missing failure-localization sidecar {rel}")
    run_rows = ingest.get("benchmark_runs")
    if isinstance(run_rows, list) and len(run_rows) > 1:
        if not (out_dir / BENCHMARK_RUN_SIDECARS_DIR).is_dir():
            errors.append(f"release-grade: missing {BENCHMARK_RUN_SIDECARS_DIR}/")
        for index, row in enumerate(run_rows):
            if not isinstance(row, dict):
                continue
            run_id = str(row.get("run_id") or row.get("case_id") or "run")
            rel = benchmark_run_sidecar_relpath(run_id)
            if not (out_dir / rel).is_file():
                errors.append(f"release-grade: missing benchmark-run sidecar {rel}")
    runs = ingest.get("benchmark_runs")
    if isinstance(runs, list):
        for index, row in enumerate(runs):
            if isinstance(row, dict) and row.get("system_admission_outcome") == "not_evaluated":
                if row.get("scientific_memory_import_status") in ("passed", "failed"):
                    errors.append(
                        f"release-grade: benchmark_runs[{index}].system_admission_outcome "
                        "must not be not_evaluated when import status is known",
                    )
    return errors


def coerce_responsible_component(raw: str | None) -> str:
    if not raw:
        return "scientific_memory"
    key = str(raw).strip()
    return RESPONSIBLE_COMPONENT_ALIASES.get(key, RESPONSIBLE_COMPONENT_ALIASES.get(key.lower(), "scientific_memory"))


def build_coverage_report(
    *,
    coverage_id: str,
    metric: str,
    numerator: float,
    denominator: float,
    source_commit: str,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    denom = max(float(denominator), 0.0)
    ratio = (float(numerator) / denom) if denom else 0.0
    body: dict[str, Any] = {
        "schema_version": "v0",
        "coverage_id": coverage_id,
        "metric": metric,
        "numerator": float(numerator),
        "denominator": denom if denom else 1.0,
        "coverage_ratio": min(1.0, max(0.0, ratio)),
        "details": details or {},
        "source_repo": SOURCE_REPO,
        "source_commit": normalize_source_commit(source_commit),
        "signature_or_digest": "",
    }
    return _with_digest(body)


def project_explain_quality_report(sm_report: dict[str, Any]) -> dict[str, Any]:
    """Map SM explain-quality row to pcs-core ExplainQualityReport.v0."""
    required = list(sm_report.get("required_sections") or [])
    raw_sections = sm_report.get("sections")
    sections: dict[str, Any] = {}
    gaps: list[dict[str, str]] = []

    if isinstance(raw_sections, dict):
        for section_id, row in raw_sections.items():
            if isinstance(row, dict):
                present = bool(row.get("present"))
                score = float(row.get("score", 1.0 if present else 0.0))
            else:
                present = bool(row)
                score = 1.0 if present else 0.0
            sections[str(section_id)] = {"present": present, "score": score}
            if not present:
                gaps.append(
                    {
                        "section_id": str(section_id),
                        "message": f"Missing explain-quality section {section_id}",
                    },
                )
    elif isinstance(raw_sections, list):
        for row in raw_sections:
            if not isinstance(row, dict):
                continue
            section_id = str(row.get("explain_quality_section_id") or "")
            if not section_id:
                continue
            rendered = bool(row.get("rendered"))
            sections[section_id] = {"present": rendered, "score": 1.0 if rendered else 0.0}
            if not rendered:
                gaps.append(
                    {
                        "section_id": section_id,
                        "message": f"Missing explain-quality section {section_id}",
                    },
                )

    for section_id in required:
        if section_id not in sections:
            sections[section_id] = {"present": False, "score": 0.0}
            gaps.append(
                {
                    "section_id": str(section_id),
                    "message": f"Missing explain-quality section {section_id}",
                },
            )

    present_count = sum(1 for row in sections.values() if row.get("present"))
    required_count = len(required) or len(sections)
    body: dict[str, Any] = {
        "schema_version": "v0",
        "report_id": str(sm_report.get("report_id") or f"explain-quality-{sm_report.get('case_id', 'case')}"),
        "suite_id": str(sm_report.get("suite_id") or ""),
        "case_id": str(sm_report.get("case_id") or ""),
        "producer_id": "scientific-memory",
        "workflow_id": str(sm_report.get("workflow_id") or PCS_WORKFLOW_ID),
        "required_sections": required,
        "sections": sections,
        "sections_present_count": int(sm_report.get("sections_present_count", present_count)),
        "sections_required_count": int(sm_report.get("sections_required_count", required_count)),
        "quality_score": float(sm_report.get("quality_score", 0.0)),
        "gaps": gaps if gaps else list(sm_report.get("gaps") or []),
        "source_repo": str(sm_report.get("source_repo") or SOURCE_REPO),
        "source_commit": normalize_source_commit(str(sm_report.get("source_commit") or "")),
        "signature_or_digest": "",
    }
    if body["gaps"] and isinstance(body["gaps"][0], str):
        body["gaps"] = [
            {"section_id": gap, "message": f"Missing explain-quality section {gap}"} for gap in body["gaps"]
        ]
    return _with_digest(body)


def _primary_failure_event(case_result: dict[str, Any]) -> dict[str, Any] | None:
    events = case_result.get("failure_events") or []
    for event in events:
        if isinstance(event, dict) and event.get("kind") in FAILURE_KINDS:
            return event
    return events[0] if events and isinstance(events[0], dict) else None


def _expected_responsible_component(case_config: dict[str, Any], expected_code: str) -> str:
    """Default responsible component by failure kind (override via case.json)."""
    if case_config.get("expected_responsible_component"):
        return coerce_responsible_component(str(case_config["expected_responsible_component"]))
    by_kind: dict[str, str] = {
        "formal_failed": "formal_kernel",
        "import_failed": "scientific_memory",
        "render_failed": "scientific_memory",
        "query_failed": "scientific_memory",
        "staleness_failed": "scientific_memory",
        "comparison_failed": "scientific_memory",
    }
    return by_kind.get(expected_code, "scientific_memory")


def _expected_failure_code(case_result: dict[str, Any], case_config: dict[str, Any]) -> str:
    if case_config.get("expected_failure_code"):
        return str(case_config["expected_failure_code"])
    expected = case_config.get("expected_failure") or case_result.get("expected_failure") or {}
    if isinstance(expected, dict):
        if expected.get("failure_kind"):
            return str(expected["failure_kind"])
        if expected.get("failure_kind") is None and expected.get("formal_focus"):
            return "formal_failed"
    if case_config.get("post_import") == "mark_stale" or case_config.get("expected_staleness"):
        return "staleness_failed"
    if case_config.get("expected_compare") or case_config.get("expected_compare_path"):
        return "comparison_failed"
    if case_config.get("failure_mode"):
        return "formal_failed" if case_config.get("formal_focus") else "render_failed"
    return ""


def build_benchmark_run(
    case_result: dict[str, Any],
    *,
    suite_id: str,
    source_commit: str,
    started_at: str | None = None,
) -> dict[str, Any]:
    """Build pcs-core BenchmarkRun.v0 for one rendering benchmark case."""
    case_id = str(case_result.get("case_id") or "")
    primary = _primary_failure_event(case_result)
    passed = bool(case_result.get("passed"))
    observed_status = "passed" if passed else "failed"
    observed_failure_code: str | None = None
    observed_component: str | None = None
    repair_hint: str | None = None

    if primary:
        observed_failure_code = str(primary.get("kind") or "")
        observed_component = coerce_responsible_component(str(primary.get("responsible_component") or ""))
        repair_hint = str(primary.get("repair_hint") or "") or None
    elif not passed:
        observed_failure_code = "render_failed"
        observed_component = "scientific_memory"

    import_failed = bool(case_result.get("import_failed"))
    sm_import = "failed" if import_failed else ("passed" if not import_failed else "not_applicable")
    if sm_import == "passed":
        system_admission_outcome = "admitted"
    elif sm_import == "failed":
        system_admission_outcome = "rejected"
    else:
        system_admission_outcome = "not_evaluated"
    if import_failed:
        sm_render = "not_applicable"
    elif case_result.get("read_model"):
        sm_render = "rendered" if passed else "incomplete"
    else:
        sm_render = "not_applicable"

    runtime_s = float(case_result.get("_runtime_seconds") or 0.0)
    duration_ms = max(int(runtime_s * 1000), 0)
    completed_at = _now()
    run_started = started_at or completed_at

    artifacts = ["read_model.json"]
    if case_result.get("failure_mode"):
        artifacts.append("failure_evidence")

    body: dict[str, Any] = {
        "schema_version": "v0",
        "run_id": f"sm-bench-run-{case_id}",
        "task_id": suite_id,
        "case_id": case_id,
        "started_at": run_started,
        "completed_at": completed_at,
        "commands": [
            {
                "command": f"scientific_memory_render_benchmark {case_id}",
                "exit_code": 0 if passed else 1,
            },
        ],
        "artifacts_produced": artifacts,
        "observed_status": observed_status,
        "observed_failure_code": observed_failure_code,
        "observed_responsible_component": observed_component,
        "observed_repair_hint": repair_hint,
        "system_admission_outcome": system_admission_outcome,
        "release_chain_status": "not_applicable",
        "certificate_status": "not_applicable",
        "scientific_memory_import_status": sm_import,
        "scientific_memory_render_status": sm_render,
        "duration_ms": duration_ms,
        "source_repo": SOURCE_REPO,
        "source_commit": normalize_source_commit(source_commit),
        "signature_or_digest": "",
    }
    return _with_digest(body)


def build_failure_localization_result(
    case_result: dict[str, Any],
    *,
    case_config: dict[str, Any],
    run: dict[str, Any],
    source_commit: str,
) -> dict[str, Any] | None:
    """Build FailureLocalizationResult.v0 when a case records evidence-layer failures."""
    primary = _primary_failure_event(case_result)
    failure_mode = bool(case_config.get("failure_mode"))
    if not primary and not failure_mode:
        return None

    expected_code = _expected_failure_code(case_result, case_config)
    observed_code = str(primary.get("kind") if primary else "")
    if not observed_code and failure_mode and case_result.get("passed"):
        observed_code = expected_code
    if not observed_code and failure_mode:
        observed_code = expected_code or "render_failed"
    expected_component = _expected_responsible_component(case_config, expected_code)
    observed_component = coerce_responsible_component(
        str((primary or {}).get("responsible_component") or expected_component),
    )
    if failure_mode and case_result.get("passed") and expected_code == "formal_failed":
        observed_component = expected_component
    localized = (not expected_code and not observed_code) or (
        expected_code == observed_code and expected_component == observed_component
    )

    body: dict[str, Any] = {
        "schema_version": "v0",
        "result_id": f"failure-loc-{run.get('run_id', case_result.get('case_id'))}",
        "run_id": str(run.get("run_id") or ""),
        "case_id": str(case_result.get("case_id") or ""),
        "expected_failure_code": expected_code,
        "observed_failure_code": observed_code,
        "expected_responsible_component": expected_component,
        "observed_responsible_component": observed_component,
        "localized_correctly": localized,
        "source_repo": SOURCE_REPO,
        "source_commit": normalize_source_commit(source_commit),
        "signature_or_digest": "",
    }
    return _with_digest(body)


def _coverage_from_cases(
    *,
    coverage_id: str,
    metric: str,
    sm_metric: str,
    cases: list[dict[str, Any]],
    source_commit: str,
    passed_key: str = "passed",
) -> dict[str, Any]:
    total = len(cases)
    if total == 0:
        return build_coverage_report(
            coverage_id=coverage_id,
            metric=metric,
            numerator=1.0,
            denominator=1.0,
            source_commit=source_commit,
            details={
                "sm_metric": sm_metric,
                "case_count": 0,
                "passed_cases": 0,
                "applicability": "not_applicable",
                "cases": [],
            },
        )
    passed = sum(1 for row in cases if row.get(passed_key))
    return build_coverage_report(
        coverage_id=coverage_id,
        metric=metric,
        numerator=float(passed),
        denominator=float(total),
        source_commit=source_commit,
        details={
            "sm_metric": sm_metric,
            "case_count": total,
            "passed_cases": passed,
            "applicability": "measured",
            "cases": [
                {
                    "case_id": row.get("case_id"),
                    "passed": row.get(passed_key),
                }
                for row in cases
            ],
        },
    )


def project_coverage_reports(
    *,
    suite_id: str,
    source_commit: str,
    rendering_report: dict[str, Any],
    query_report: dict[str, Any],
    failed_report: dict[str, Any],
    case_results: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Map SM v0 coverage reports to pcs-core CoverageReport.v0 list."""
    rendering_cases = list(rendering_report.get("cases") or [])
    query_cases = list(query_report.get("cases") or [])
    failed_cases = list(failed_report.get("cases") or [])

    comparison_cases = [
        row
        for row in case_results
        if isinstance(row.get("compare"), dict) and not row["compare"].get("skipped")
    ]
    staleness_cases = [
        row for row in case_results if (row.get("metrics") or {}).get("staleness_detected") is not None
    ]

    return [
        _coverage_from_cases(
            coverage_id=f"{suite_id}-interpretability",
            metric="scientific_memory_interpretability",
            sm_metric="scientific_memory_interpretability",
            cases=rendering_cases,
            source_commit=source_commit,
        ),
        _coverage_from_cases(
            coverage_id=f"{suite_id}-query-correctness",
            metric="scientific_memory_interpretability",
            sm_metric="query_correctness",
            cases=query_cases,
            source_commit=source_commit,
        ),
        _coverage_from_cases(
            coverage_id=f"{suite_id}-failed-release-rendering",
            metric="failure_localization",
            sm_metric="failed_release_rendering",
            cases=failed_cases,
            source_commit=source_commit,
        ),
        _coverage_from_cases(
            coverage_id=f"{suite_id}-release-comparison",
            metric="scientific_memory_interpretability",
            sm_metric="release_comparison",
            cases=[
                {
                    "case_id": row.get("case_id"),
                    "passed": (row.get("compare") or {}).get("passed", row.get("passed")),
                }
                for row in comparison_cases
            ],
            source_commit=source_commit,
        ),
        _coverage_from_cases(
            coverage_id=f"{suite_id}-staleness-detection",
            metric="repair_hint_quality",
            sm_metric="staleness_detection",
            cases=[
                {
                    "case_id": row.get("case_id"),
                    "passed": not any(
                        e.get("kind") == "staleness_failed"
                        for e in (row.get("failure_events") or [])
                        if isinstance(e, dict)
                    ),
                }
                for row in staleness_cases
            ],
            source_commit=source_commit,
        ),
    ]


def explain_quality_sidecar_relpath(report_id: str) -> str:
    safe = "".join(ch if ch.isalnum() or ch in "-_" else "-" for ch in report_id)
    return f"{EXPLAIN_QUALITY_SIDECARS_DIR}/{safe}.v0.json"


def coverage_sidecar_relpath(coverage_id: str) -> str:
    safe = "".join(ch if ch.isalnum() or ch in "-_" else "-" for ch in coverage_id)
    return f"{COVERAGE_SIDECARS_DIR}/{safe}.v0.json"


def benchmark_run_sidecar_relpath(run_id: str) -> str:
    safe = "".join(ch if ch.isalnum() or ch in "-_" else "-" for ch in run_id)
    return f"{BENCHMARK_RUN_SIDECARS_DIR}/{safe}.v0.json"


def failure_localization_sidecar_relpath(result_id: str) -> str:
    safe = "".join(ch if ch.isalnum() or ch in "-_" else "-" for ch in result_id)
    return f"{FAILURE_LOCALIZATION_SIDECARS_DIR}/{safe}.v0.json"


def build_benchmark_artifact_ref(
    *,
    artifact_type: str,
    path: str,
    embedded: dict[str, Any],
    source_commit: str,
    role: str = "producer_export",
) -> dict[str, Any]:
    """Build BenchmarkArtifactRef.v0 for on-disk provenance of an embedded ingest object."""
    digest = str(embedded.get("signature_or_digest") or "")
    body: dict[str, Any] = {
        "schema_version": "v0",
        "artifact_type": artifact_type,
        "path": path.replace("\\", "/"),
        "sha256": digest,
        "role": role,
        "source_repo": SOURCE_REPO,
        "source_commit": normalize_source_commit(source_commit),
        "signature_or_digest": "",
    }
    return _with_digest(body)


def build_artifact_refs_for_ingest(
    *,
    explain_quality_reports: list[dict[str, Any]],
    coverage_reports: list[dict[str, Any]] | None = None,
    benchmark_runs: list[dict[str, Any]] | None = None,
    failure_localization_reports: list[dict[str, Any]] | None = None,
    source_commit: str,
    benchmark_run_aggregate_path: str = "benchmark_run.v0.json",
) -> list[dict[str, Any]]:
    """Build BenchmarkArtifactRef.v0 rows for embedded ingest objects and on-disk sidecars."""
    refs: list[dict[str, Any]] = []
    run_rows = [row for row in (benchmark_runs or []) if isinstance(row, dict)]
    if len(run_rows) == 1:
        refs.append(
            build_benchmark_artifact_ref(
                artifact_type="BenchmarkRun.v0",
                path=benchmark_run_aggregate_path,
                embedded=run_rows[0],
                source_commit=source_commit,
                role="producer_export",
            ),
        )
    for run in run_rows:
        run_id = str(run.get("run_id") or run.get("case_id") or "run")
        path = (
            benchmark_run_aggregate_path
            if len(run_rows) == 1
            else benchmark_run_sidecar_relpath(run_id)
        )
        if len(run_rows) > 1:
            refs.append(
                build_benchmark_artifact_ref(
                    artifact_type="BenchmarkRun.v0",
                    path=path,
                    embedded=run,
                    source_commit=source_commit,
                    role="producer_export",
                ),
            )
    for report in explain_quality_reports:
        if not isinstance(report, dict):
            continue
        report_id = str(report.get("report_id") or report.get("case_id") or "case")
        refs.append(
            build_benchmark_artifact_ref(
                artifact_type="ExplainQualityReport.v0",
                path=explain_quality_sidecar_relpath(report_id),
                embedded=report,
                source_commit=source_commit,
                role="producer_export",
            ),
        )
    for row in coverage_reports or []:
        if not isinstance(row, dict):
            continue
        coverage_id = str(row.get("coverage_id") or row.get("metric") or "coverage")
        refs.append(
            build_benchmark_artifact_ref(
                artifact_type="CoverageReport.v0",
                path=coverage_sidecar_relpath(coverage_id),
                embedded=row,
                source_commit=source_commit,
                role="producer_export",
            ),
        )
    for row in failure_localization_reports or []:
        if not isinstance(row, dict):
            continue
        result_id = str(row.get("result_id") or row.get("case_id") or "failure-loc")
        refs.append(
            build_benchmark_artifact_ref(
                artifact_type="FailureLocalizationResult.v0",
                path=failure_localization_sidecar_relpath(result_id),
                embedded=row,
                source_commit=source_commit,
                role="producer_export",
            ),
        )
    return refs


def write_explain_quality_sidecars(
    out_dir: Path,
    explain_quality_reports: list[dict[str, Any]],
) -> dict[str, str]:
    """Write one ExplainQualityReport.v0 JSON file per embedded ingest row."""
    sidecar_dir = out_dir / EXPLAIN_QUALITY_SIDECARS_DIR
    sidecar_dir.mkdir(parents=True, exist_ok=True)
    written: dict[str, str] = {}
    for report in explain_quality_reports:
        report_id = str(report.get("report_id") or report.get("case_id") or "case")
        rel = explain_quality_sidecar_relpath(report_id)
        path = out_dir / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        written[report_id] = rel
    return written


def write_benchmark_run_sidecars(
    out_dir: Path,
    benchmark_runs: list[dict[str, Any]],
) -> dict[str, str]:
    """Write one BenchmarkRun.v0 JSON file per embedded ingest row."""
    sidecar_dir = out_dir / BENCHMARK_RUN_SIDECARS_DIR
    sidecar_dir.mkdir(parents=True, exist_ok=True)
    written: dict[str, str] = {}
    for row in benchmark_runs:
        if not isinstance(row, dict):
            continue
        run_id = str(row.get("run_id") or row.get("case_id") or "run")
        rel = benchmark_run_sidecar_relpath(run_id)
        path = out_dir / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(row, indent=2) + "\n", encoding="utf-8")
        written[run_id] = rel
    return written


def write_failure_localization_sidecars(
    out_dir: Path,
    failure_localization_reports: list[dict[str, Any]],
) -> dict[str, str]:
    """Write one FailureLocalizationResult.v0 JSON file per embedded ingest row."""
    sidecar_dir = out_dir / FAILURE_LOCALIZATION_SIDECARS_DIR
    sidecar_dir.mkdir(parents=True, exist_ok=True)
    written: dict[str, str] = {}
    for row in failure_localization_reports:
        if not isinstance(row, dict):
            continue
        result_id = str(row.get("result_id") or row.get("case_id") or "failure-loc")
        rel = failure_localization_sidecar_relpath(result_id)
        path = out_dir / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(row, indent=2) + "\n", encoding="utf-8")
        written[result_id] = rel
    return written


def write_coverage_sidecars(
    out_dir: Path,
    coverage_reports: list[dict[str, Any]],
) -> dict[str, str]:
    """Write one CoverageReport.v0 JSON file per embedded ingest row."""
    sidecar_dir = out_dir / COVERAGE_SIDECARS_DIR
    sidecar_dir.mkdir(parents=True, exist_ok=True)
    written: dict[str, str] = {}
    for row in coverage_reports:
        if not isinstance(row, dict):
            continue
        coverage_id = str(row.get("coverage_id") or row.get("metric") or "coverage")
        rel = coverage_sidecar_relpath(coverage_id)
        path = out_dir / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(row, indent=2) + "\n", encoding="utf-8")
        written[coverage_id] = rel
    return written


def build_producer_commands(
    *,
    cases_path: str,
    out_dir: str,
    pcs_core_path: str | None = None,
    release_grade: bool = False,
    passed: bool = True,
) -> list[dict[str, Any]]:
    """Record the live producer CLI invocation in PcsBenchIngest.v0.commands."""
    parts = [
        "sm-pipeline pcs-benchmark-rendering",
        f"--cases {cases_path}",
        f"--out {out_dir}",
    ]
    if pcs_core_path:
        parts.append(f"--validate-pcs-core-output {pcs_core_path}")
    if release_grade:
        parts.append("--release-grade")
    return [{"command": " ".join(parts), "exit_code": 0 if passed else 1}]


def build_embedded_pcs_bench_ingest(
    *,
    suite_id: str,
    source_commit: str,
    benchmark_run_doc: dict[str, Any],
    v0_reports: dict[str, dict[str, Any]],
    case_results: list[dict[str, Any]],
    case_configs: dict[str, dict[str, Any]] | None = None,
    artifact_refs: list[dict[str, Any]] | None = None,
    producer_commands: list[dict[str, Any]] | None = None,
    producer_logs: list[str] | None = None,
) -> dict[str, Any]:
    """Assemble pcs-core PcsBenchIngest.v0 with embedded canonical objects."""
    case_configs = case_configs or {}
    started_at = str(benchmark_run_doc.get("generated_at") or _now())
    commit = normalize_source_commit(source_commit)

    rendering_report = v0_reports.get("rendering_coverage_report.v0.json") or {}
    query_report = v0_reports.get("query_coverage_report.v0.json") or {}
    failed_report = v0_reports.get("failed_release_rendering_report.v0.json") or {}
    eq_bundle = v0_reports.get("explain_quality_report.v0.json") or {}

    benchmark_runs = [
        build_benchmark_run(
            row,
            suite_id=suite_id,
            source_commit=commit,
            started_at=started_at,
        )
        for row in case_results
    ]

    failure_localization_reports: list[dict[str, Any]] = []
    for row in case_results:
        case_id = str(row.get("case_id") or "")
        run = next((r for r in benchmark_runs if r.get("case_id") == case_id), None)
        if not run:
            continue
        loc = build_failure_localization_result(
            row,
            case_config=case_configs.get(case_id, {}),
            run=run,
            source_commit=commit,
        )
        if loc:
            failure_localization_reports.append(loc)

    explain_rows = eq_bundle.get("reports") if isinstance(eq_bundle.get("reports"), list) else []
    if not explain_rows:
        explain_rows = [
            row.get("explain_quality_coverage")
            for row in (rendering_report.get("cases") or [])
            if isinstance(row.get("explain_quality_coverage"), dict)
        ]
        explain_rows.extend(
            row.get("explain_quality_coverage")
            for row in (failed_report.get("cases") or [])
            if isinstance(row.get("explain_quality_coverage"), dict)
        )

    explain_quality_reports = [project_explain_quality_report(row) for row in explain_rows if isinstance(row, dict)]

    coverage_reports = project_coverage_reports(
        suite_id=suite_id,
        source_commit=commit,
        rendering_report=rendering_report,
        query_report=query_report,
        failed_report=failed_report,
        case_results=case_results,
    )

    refs = list(artifact_refs or [])
    if not refs and (
        explain_quality_reports
        or coverage_reports
        or benchmark_runs
        or failure_localization_reports
    ):
        refs = build_artifact_refs_for_ingest(
            explain_quality_reports=explain_quality_reports,
            coverage_reports=coverage_reports,
            benchmark_runs=benchmark_runs,
            failure_localization_reports=failure_localization_reports,
            source_commit=commit,
        )

    passed = bool(benchmark_run_doc.get("passed"))
    commands = list(producer_commands or [])
    if not commands:
        commands = [
            {
                "command": "scientific_memory_render_benchmark",
                "exit_code": 0 if passed else 1,
            },
        ]
    body: dict[str, Any] = {
        "schema_version": "v0",
        "producer_id": "scientific-memory",
        "suite_id": suite_id,
        "workflow_id": PCS_WORKFLOW_ID,
        "benchmark_runs": benchmark_runs,
        "coverage_reports": coverage_reports,
        "failure_localization_reports": failure_localization_reports,
        "explain_quality_reports": explain_quality_reports,
        "profile_coverage_reports": [],
        "commands": commands,
        "logs": list(producer_logs or []),
        "source_repo": SOURCE_REPO,
        "source_commit": commit,
        "signature_or_digest": "",
    }
    if refs:
        body["artifact_refs"] = refs
    return _with_digest(body)


LEGACY_INGEST_TOP_LEVEL_KEYS: frozenset[str] = frozenset(
    {
        "passed",
        "query_results",
        "rendering_reports",
        "failure_summary",
        "failure_kinds",
        "ingest_contract",
    },
)


def validate_embedded_ingest_contract(
    ingest: dict[str, Any],
    *,
    out_dir: Path | None = None,
) -> list[str]:
    """Structural checks for pcs-core embedded ingest (before schema/semantic validation)."""
    errors: list[str] = []

    for key in LEGACY_INGEST_TOP_LEVEL_KEYS:
        if key in ingest:
            errors.append(f"pcs_bench_ingest.v0.json: legacy top-level field {key!r} must not be present")

    if str(ingest.get("producer_id") or "") != "scientific-memory":
        errors.append("pcs_bench_ingest.v0.json: producer_id must be 'scientific-memory'")
    if str(ingest.get("workflow_id") or "") != PCS_WORKFLOW_ID:
        errors.append(f"pcs_bench_ingest.v0.json: workflow_id must be {PCS_WORKFLOW_ID!r}")

    runs = ingest.get("benchmark_runs")
    if isinstance(runs, list):
        for index, row in enumerate(runs):
            if not isinstance(row, dict):
                errors.append(f"benchmark_runs[{index}]: expected object")
                continue
            if "path" in row and "run_id" not in row:
                errors.append(f"benchmark_runs[{index}]: path reference; embed BenchmarkRun.v0")
            elif "run_id" not in row:
                errors.append(f"benchmark_runs[{index}]: missing run_id")

    coverage = ingest.get("coverage_reports")
    if isinstance(coverage, list):
        sm_metrics: set[str] = set()
        for index, row in enumerate(coverage):
            if not isinstance(row, dict):
                continue
            if "path" in row and "coverage_id" not in row:
                errors.append(f"coverage_reports[{index}]: path reference; embed CoverageReport.v0")
            details = row.get("details") if isinstance(row.get("details"), dict) else {}
            sm_metric = str(details.get("sm_metric") or "")
            if sm_metric:
                sm_metrics.add(sm_metric)
        missing = set(SM_COVERAGE_METRICS) - sm_metrics
        if missing:
            errors.append(
                f"coverage_reports: missing sm_metric projections: {', '.join(sorted(missing))}",
            )

    explain = ingest.get("explain_quality_reports")
    if isinstance(explain, list):
        for index, row in enumerate(explain):
            if not isinstance(row, dict):
                continue
            if isinstance(row.get("sections"), list):
                errors.append(
                    f"explain_quality_reports[{index}]: sections must be object keyed by section id",
                )
            if row.get("gaps") and isinstance(row["gaps"][0], str):
                errors.append(
                    f"explain_quality_reports[{index}]: gaps must be {{section_id, message}} objects",
                )

    refs = ingest.get("artifact_refs")
    explain_rows = explain if isinstance(explain, list) else []
    coverage_rows = coverage if isinstance(coverage, list) else []
    producer_embedded = bool(explain_rows or coverage_rows)
    if producer_embedded and not refs:
        errors.append(
            "pcs_bench_ingest.v0.json: artifact_refs required when explain_quality_reports "
            "or coverage_reports are embedded",
        )
    if isinstance(refs, list):
        ref_digests = {
            (str(ref.get("artifact_type")), str(ref.get("sha256")))
            for ref in refs
            if isinstance(ref, dict)
        }
        for index, row in enumerate(explain_rows):
            if not isinstance(row, dict):
                continue
            digest = row.get("signature_or_digest")
            if isinstance(digest, str) and ("ExplainQualityReport.v0", digest) not in ref_digests:
                errors.append(
                    f"explain_quality_reports[{index}]: no artifact_refs entry for digest {digest}",
                )
        for index, row in enumerate(coverage_rows):
            if not isinstance(row, dict):
                continue
            digest = row.get("signature_or_digest")
            if isinstance(digest, str) and ("CoverageReport.v0", digest) not in ref_digests:
                errors.append(
                    f"coverage_reports[{index}]: no artifact_refs entry for digest {digest}",
                )
        run_rows = ingest.get("benchmark_runs")
        if isinstance(run_rows, list):
            for index, row in enumerate(run_rows):
                if not isinstance(row, dict):
                    continue
                digest = row.get("signature_or_digest")
                if isinstance(digest, str) and ("BenchmarkRun.v0", digest) not in ref_digests:
                    errors.append(
                        f"benchmark_runs[{index}]: no artifact_refs entry for digest {digest}",
                    )
        fl_rows = ingest.get("failure_localization_reports")
        if isinstance(fl_rows, list):
            for index, row in enumerate(fl_rows):
                if not isinstance(row, dict):
                    continue
                digest = row.get("signature_or_digest")
                if isinstance(digest, str) and ("FailureLocalizationResult.v0", digest) not in ref_digests:
                    errors.append(
                        f"failure_localization_reports[{index}]: no artifact_refs entry for digest {digest}",
                    )
        if out_dir is not None:
            for index, ref in enumerate(refs):
                if not isinstance(ref, dict):
                    continue
                rel = str(ref.get("path") or "").replace("\\", "/")
                if rel and not (out_dir / rel).is_file():
                    errors.append(f"artifact_refs[{index}]: missing on-disk file {rel}")

    return errors
