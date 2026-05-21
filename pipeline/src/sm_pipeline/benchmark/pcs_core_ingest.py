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


def _expected_failure_code(case_result: dict[str, Any], case_config: dict[str, Any]) -> str:
    if case_config.get("expected_failure_code"):
        return str(case_config["expected_failure_code"])
    expected = case_config.get("expected_failure") or case_result.get("expected_failure") or {}
    if isinstance(expected, dict):
        if expected.get("failure_kind"):
            return str(expected["failure_kind"])
        if expected.get("failure_kind") is None and expected.get("formal_focus"):
            return "formal_failed"
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
        "system_admission_outcome": "not_evaluated",
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
    if not primary and not case_config.get("failure_mode"):
        return None

    expected_code = _expected_failure_code(case_result, case_config)
    observed_code = str(primary.get("kind") if primary else "")
    if not observed_code and case_config.get("failure_mode") and case_result.get("passed"):
        observed_code = expected_code
    if not observed_code and case_config.get("failure_mode"):
        observed_code = "render_failed"
    expected_component = coerce_responsible_component(
        str(case_config.get("expected_responsible_component") or "scientific_memory"),
    )
    observed_component = coerce_responsible_component(
        str((primary or {}).get("responsible_component") or "scientific_memory"),
    )
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
    passed = sum(1 for row in cases if row.get(passed_key))
    return build_coverage_report(
        coverage_id=coverage_id,
        metric=metric,
        numerator=float(passed),
        denominator=float(total or 1),
        source_commit=source_commit,
        details={
            "sm_metric": sm_metric,
            "case_count": total,
            "passed_cases": passed,
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
            ]
            or [{"case_id": "none", "passed": True}],
            source_commit=source_commit,
        ),
    ]


def explain_quality_sidecar_relpath(report_id: str) -> str:
    safe = "".join(ch if ch.isalnum() or ch in "-_" else "-" for ch in report_id)
    return f"{EXPLAIN_QUALITY_SIDECARS_DIR}/{safe}.v0.json"


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
    source_commit: str,
) -> list[dict[str, Any]]:
    """pcs-core requires artifact_refs covering each embedded ExplainQualityReport.v0 digest."""
    refs: list[dict[str, Any]] = []
    for report in explain_quality_reports:
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


def build_embedded_pcs_bench_ingest(
    *,
    suite_id: str,
    source_commit: str,
    benchmark_run_doc: dict[str, Any],
    v0_reports: dict[str, dict[str, Any]],
    case_results: list[dict[str, Any]],
    case_configs: dict[str, dict[str, Any]] | None = None,
    artifact_refs: list[dict[str, Any]] | None = None,
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

    refs = list(artifact_refs or [])
    if not refs and explain_quality_reports:
        refs = build_artifact_refs_for_ingest(
            explain_quality_reports=explain_quality_reports,
            source_commit=commit,
        )

    coverage_reports = project_coverage_reports(
        suite_id=suite_id,
        source_commit=commit,
        rendering_report=rendering_report,
        query_report=query_report,
        failed_report=failed_report,
        case_results=case_results,
    )

    passed = bool(benchmark_run_doc.get("passed"))
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
        "commands": [
            {
                "command": "scientific_memory_render_benchmark",
                "exit_code": 0 if passed else 1,
            },
        ],
        "logs": [],
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
    if explain_rows and not refs:
        errors.append("pcs_bench_ingest.v0.json: artifact_refs required when explain_quality_reports are embedded")
    if isinstance(refs, list) and explain_rows:
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
        if out_dir is not None:
            for index, ref in enumerate(refs):
                if not isinstance(ref, dict):
                    continue
                rel = str(ref.get("path") or "").replace("\\", "/")
                if rel and not (out_dir / rel).is_file():
                    errors.append(f"artifact_refs[{index}]: missing on-disk file {rel}")

    return errors
