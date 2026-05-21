"""Split PCS rendering benchmark results into v0 report artifacts for pcs-bench."""

from __future__ import annotations

import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from sm_pipeline.benchmark.bench_registry import build_run_suite_manifest, validate_suite_id
from sm_pipeline.benchmark.failure_taxonomy import FAILURE_KINDS, failure_messages, summarize_failure_kinds
from sm_pipeline.benchmark.pcs_core_coverage import (
    EXPLAIN_QUALITY_SECTION_IDS,
    SOURCE_REPO,
    build_explain_quality_report,
    suite_id_for_cases_path,
)
from sm_pipeline.pcs_validate.canonical_hash import canonical_hash
from sm_pipeline.pcs_validate.validator import validator_for

V0_REPORT_FILENAMES: tuple[str, ...] = (
    "benchmark_run.v0.json",
    "rendering_coverage_report.v0.json",
    "query_coverage_report.v0.json",
    "failed_release_rendering_report.v0.json",
)

V0_SCHEMAS = {
    "benchmark_run.v0.json": "benchmark/BenchmarkRun.v0.schema.json",
    "rendering_coverage_report.v0.json": "benchmark/RenderingCoverageReport.v0.schema.json",
    "query_coverage_report.v0.json": "benchmark/QueryCoverageReport.v0.schema.json",
    "failed_release_rendering_report.v0.json": "benchmark/FailedReleaseRenderingReport.v0.schema.json",
    "pcs_bench_ingest.v0.json": "benchmark/PcsBenchIngest.v0.schema.json",
    "explain_quality_report.v0.json": "benchmark/ExplainQualityReport.v0.schema.json",
}

PCS_BENCH_INGEST_FILENAME = "pcs_bench_ingest.v0.json"
EXPLAIN_QUALITY_REPORT_FILENAME = "explain_quality_report.v0.json"
BENCH_SUITE_MANIFEST_FILENAME = "bench_suite_manifest.v0.json"
LEGACY_PAYLOAD_FILENAME = "pcs_bench_payload.json"
PCS_WORKFLOW_ID = "pcs.scientific_memory"


def _now() -> str:
    return datetime.now(UTC).isoformat()


def normalize_benchmark_out_dir(raw: str) -> str:
    """Accept a path or mistaken ``OUT=benchmark_runs/...`` from shell/just docs."""
    text = raw.strip()
    if text.upper().startswith("OUT="):
        return text.split("=", 1)[1].strip()
    return text


def resolve_source_commit(repo_root: Path) -> str:
    try:
        proc = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=True,
            timeout=10,
        )
        return proc.stdout.strip() or "unknown"
    except (OSError, subprocess.SubprocessError):
        return "unknown"


def _aggregate_failure_summary(case_results: list[dict[str, Any]]) -> dict[str, Any]:
    by_kind: dict[str, int] = {kind: 0 for kind in FAILURE_KINDS}
    events: list[dict[str, Any]] = []
    for result in case_results:
        for event in result.get("failure_events") or []:
            if not isinstance(event, dict):
                continue
            events.append({**event, "case_id": result.get("case_id")})
            kind = str(event.get("kind") or "")
            if kind in by_kind:
                by_kind[kind] += 1
    return {
        "by_kind": by_kind,
        "total_events": len(events),
        "events": events[:50],
    }


def build_v0_reports(
    case_results: list[dict[str, Any]],
    *,
    repo_root: Path,
    cases_path: Path,
    aggregate_failures: list[str],
    metrics: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    """Build pcs-bench-facing report documents."""
    suite_id = suite_id_for_cases_path(str(cases_path))
    source_commit = resolve_source_commit(repo_root)
    failure_summary = _aggregate_failure_summary(case_results)

    rendering_cases: list[dict[str, Any]] = []
    explain_quality_reports: list[dict[str, Any]] = []

    for result in case_results:
        if result.get("import_failed"):
            continue
        read_model = result.get("read_model") if isinstance(result.get("read_model"), dict) else {}
        section_report = result.get("section_coverage") or {}
        case_id = str(result.get("case_id") or "")
        claim_id = str(result.get("claim_id") or "")
        eq_report = build_explain_quality_report(
            case_id=case_id,
            claim_id=claim_id,
            read_model=read_model,
            section_coverage=section_report,
            suite_id=suite_id,
            source_commit=source_commit,
        )
        explain_quality_reports.append(eq_report)
        case_row = {
            "case_id": case_id,
            "claim_id": claim_id,
            "release_id": result.get("release_id"),
            "passed": result.get("passed"),
            "failures": result.get("failures") or [],
            "failure_kinds": result.get("failure_kinds")
            or summarize_failure_kinds(result.get("failure_events") or []),
            "section_coverage": section_report,
            "explain_quality_coverage": eq_report,
            "render_metrics": {
                k: v
                for k, v in (result.get("metrics") or {}).items()
                if k
                not in (
                    "query_responses_correct",
                    "release_comparison_correct",
                    "failure_evidence_rendered",
                )
            },
        }
        if result.get("failure_mode"):
            continue
        rendering_cases.append(case_row)

    query_cases = []
    for result in case_results:
        queries = result.get("queries") or {}
        query_cases.append(
            {
                "case_id": result.get("case_id"),
                "passed": queries.get("passed", result.get("passed")),
                "failure_kinds": result.get("failure_kinds") or {},
                "queries": queries.get("queries") or [],
                "compare": result.get("compare") if not result.get("compare", {}).get("skipped") else None,
            },
        )

    failed_rendering_cases = []
    for result in case_results:
        if not result.get("failure_mode"):
            continue
        eq_cov = next(
            (
                row
                for row in explain_quality_reports
                if row.get("case_id") == result.get("case_id")
            ),
            None,
        )
        failed_rendering_cases.append(
            {
                "case_id": result.get("case_id"),
                "claim_id": result.get("claim_id"),
                "passed": result.get("passed"),
                "failures": result.get("failures") or [],
                "failure_kinds": result.get("failure_kinds") or {},
                "failure_events": result.get("failure_events") or [],
                "failure_evidence": result.get("failure_evidence") or {},
                "explain_quality_coverage": eq_cov,
            },
        )

    benchmark_run = {
        "schema_version": "BenchmarkRun.v0",
        "benchmark_id": "pcs_rendering",
        "suite_id": suite_id,
        "generated_at": _now(),
        "repo_root": str(repo_root.resolve()),
        "cases_path": str(cases_path.resolve()),
        "passed": not aggregate_failures,
        "case_count": len(case_results),
        "failures": aggregate_failures,
        "failure_events": failure_summary.get("events") or [],
        "failure_summary": failure_summary,
        "metrics": metrics,
        "cases": [
            {
                "case_id": c.get("case_id"),
                "claim_id": c.get("claim_id"),
                "release_id": c.get("release_id"),
                "passed": c.get("passed"),
                "failures": c.get("failures") or [],
                "failure_kinds": c.get("failure_kinds") or {},
                "failure_events": c.get("failure_events") or [],
                "failure_mode": bool(c.get("failure_mode")),
            }
            for c in case_results
        ],
    }

    rendering_report = {
        "schema_version": "RenderingCoverageReport.v0",
        "generated_at": _now(),
        "suite_id": suite_id,
        "producer_id": "scientific-memory",
        "passed": all(c.get("passed") for c in rendering_cases) if rendering_cases else True,
        "case_count": len(rendering_cases),
        "explain_quality_section_ids": list(EXPLAIN_QUALITY_SECTION_IDS),
        "cases": rendering_cases,
    }

    query_report = {
        "schema_version": "QueryCoverageReport.v0",
        "generated_at": _now(),
        "passed": all(c.get("passed") for c in query_cases) if query_cases else True,
        "case_count": len(query_cases),
        "cases": query_cases,
    }

    failed_report = {
        "schema_version": "FailedReleaseRenderingReport.v0",
        "generated_at": _now(),
        "passed": all(c.get("passed") for c in failed_rendering_cases) if failed_rendering_cases else True,
        "case_count": len(failed_rendering_cases),
        "cases": failed_rendering_cases,
    }

    explain_quality_bundle = {
        "schema_version": "v0",
        "suite_id": suite_id,
        "producer_id": "scientific-memory",
        "source_repo": SOURCE_REPO,
        "source_commit": source_commit,
        "reports": explain_quality_reports,
    }
    explain_quality_bundle["signature_or_digest"] = canonical_hash(explain_quality_bundle)

    return {
        "benchmark_run.v0.json": benchmark_run,
        "rendering_coverage_report.v0.json": rendering_report,
        "query_coverage_report.v0.json": query_report,
        "failed_release_rendering_report.v0.json": failed_report,
        EXPLAIN_QUALITY_REPORT_FILENAME: explain_quality_bundle,
    }


def validate_v0_reports(repo_root: Path, reports: dict[str, dict[str, Any]]) -> list[str]:
    """Validate report payloads against schemas/pcs/benchmark/*.schema.json."""
    errors: list[str] = []
    for filename, payload in reports.items():
        schema_rel = V0_SCHEMAS.get(filename)
        if not schema_rel:
            continue
        try:
            validator = validator_for(schema_rel, repo_root)
        except FileNotFoundError as exc:
            errors.append(f"{filename}: {exc}")
            continue
        targets: list[dict[str, Any]] = [payload]
        if filename == EXPLAIN_QUALITY_REPORT_FILENAME:
            targets = [
                row
                for row in (payload.get("reports") or [])
                if isinstance(row, dict)
            ]
        for target in targets:
            for err in sorted(validator.iter_errors(target), key=lambda item: item.path):
                path = "/".join(str(p) for p in err.path) or "(root)"
                label = filename if target is payload else f"{filename}/{target.get('report_id', 'case')}"
                errors.append(f"{label}: {path}: {err.message}")
    return errors


def write_v0_reports(out_dir: Path, reports: dict[str, dict[str, Any]]) -> dict[str, str]:
    out_dir.mkdir(parents=True, exist_ok=True)
    paths: dict[str, str] = {}
    for filename, payload in reports.items():
        path = out_dir / filename
        path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        paths[filename] = str(path)
    return paths


def build_pcs_bench_ingest(
    *,
    benchmark_run: dict[str, Any],
    out_dir: Path,
    artifact_paths: dict[str, str],
    explain_quality_bundle: dict[str, Any],
    suite_id: str,
    source_commit: str,
) -> dict[str, Any]:
    """Canonical pcs-bench ingest manifest (stable integration point)."""
    run_path = artifact_paths.get("benchmark_run.v0.json") or str(out_dir / "benchmark_run.v0.json")
    coverage_path = artifact_paths.get("rendering_coverage_report.v0.json") or str(
        out_dir / "rendering_coverage_report.v0.json",
    )
    query_path = artifact_paths.get("query_coverage_report.v0.json") or str(
        out_dir / "query_coverage_report.v0.json",
    )
    failed_path = artifact_paths.get("failed_release_rendering_report.v0.json") or str(
        out_dir / "failed_release_rendering_report.v0.json",
    )
    eq_path = artifact_paths.get(EXPLAIN_QUALITY_REPORT_FILENAME) or str(
        out_dir / EXPLAIN_QUALITY_REPORT_FILENAME,
    )

    ingest: dict[str, Any] = {
        "schema_version": "v0",
        "producer_id": "scientific-memory",
        "suite_id": suite_id,
        "workflow_id": PCS_WORKFLOW_ID,
        "passed": bool(benchmark_run.get("passed")),
        "benchmark_runs": [
            {
                "benchmark_run_id": benchmark_run.get("benchmark_id") or "pcs_rendering",
                "path": run_path,
                "passed": bool(benchmark_run.get("passed")),
                "case_count": int(benchmark_run.get("case_count") or 0),
                "generated_at": benchmark_run.get("generated_at"),
            },
        ],
        "coverage_reports": [
            {
                "coverage_report_id": "rendering-coverage",
                "path": coverage_path,
                "explain_quality_section_ids": list(EXPLAIN_QUALITY_SECTION_IDS),
            },
        ],
        "explain_quality_reports": [
            {
                "report_id": row.get("report_id"),
                "case_id": row.get("case_id"),
                "claim_id": row.get("claim_id"),
                "bundle_path": eq_path,
                "path": eq_path,
                "quality_score": row.get("quality_score"),
                "gaps": row.get("gaps") or [],
                "explain_quality_section_ids": list(EXPLAIN_QUALITY_SECTION_IDS),
            }
            for row in (explain_quality_bundle.get("reports") or [])
            if isinstance(row, dict)
        ],
        "ingest_contract": "pcs-bench/scientific-memory/v1",
        "query_results": [
            {
                "query_report_id": "query-coverage",
                "path": query_path,
            },
        ],
        "rendering_reports": [
            {
                "rendering_report_id": "failed-release-rendering",
                "path": failed_path,
            },
        ],
        "failure_summary": benchmark_run.get("failure_summary") or {},
        "failure_kinds": list(FAILURE_KINDS),
        "source_repo": SOURCE_REPO,
        "source_commit": source_commit,
    }
    ingest["signature_or_digest"] = canonical_hash(ingest)
    return ingest


def write_pcs_bench_artifacts(
    out_dir: Path,
    *,
    repo_root: Path,
    v0_reports: dict[str, dict[str, Any]],
    artifact_paths: dict[str, str],
) -> dict[str, str]:
    """Write pcs_bench_ingest.v0.json (canonical) and pcs_bench_payload.json (legacy alias)."""
    benchmark_run = v0_reports["benchmark_run.v0.json"]
    eq_bundle = v0_reports.get(EXPLAIN_QUALITY_REPORT_FILENAME) or {}
    suite_id = str(benchmark_run.get("suite_id") or suite_id_for_cases_path(""))
    source_commit = str(eq_bundle.get("source_commit") or resolve_source_commit(repo_root))

    suite_err = validate_suite_id(repo_root, suite_id)
    if suite_err:
        raise ValueError(suite_err)

    ingest = build_pcs_bench_ingest(
        benchmark_run=benchmark_run,
        out_dir=out_dir,
        artifact_paths=artifact_paths,
        explain_quality_bundle=eq_bundle,
        suite_id=suite_id,
        source_commit=source_commit,
    )
    ingest_path = out_dir / PCS_BENCH_INGEST_FILENAME
    ingest_path.write_text(json.dumps(ingest, indent=2) + "\n", encoding="utf-8")
    paths = {PCS_BENCH_INGEST_FILENAME: str(ingest_path)}

    run_manifest = build_run_suite_manifest(
        suite_id=suite_id,
        out_dir=out_dir,
        ingest_path=ingest_path,
        passed=bool(ingest.get("passed")),
    )
    manifest_path = out_dir / BENCH_SUITE_MANIFEST_FILENAME
    manifest_path.write_text(json.dumps(run_manifest, indent=2) + "\n", encoding="utf-8")
    paths[BENCH_SUITE_MANIFEST_FILENAME] = str(manifest_path)

    legacy = {
        "schema_version": "v0",
        "producer_id": "scientific-memory",
        "suite_id": suite_id,
        "passed": ingest["passed"],
        "ingest_manifest": PCS_BENCH_INGEST_FILENAME,
        "artifacts": {
            "benchmark_run.v0.json": artifact_paths.get("benchmark_run.v0.json"),
            "rendering_coverage_report.v0.json": artifact_paths.get("rendering_coverage_report.v0.json"),
            "query_coverage_report.v0.json": artifact_paths.get("query_coverage_report.v0.json"),
            "failed_release_rendering_report.v0.json": artifact_paths.get(
                "failed_release_rendering_report.v0.json",
            ),
            EXPLAIN_QUALITY_REPORT_FILENAME: artifact_paths.get(EXPLAIN_QUALITY_REPORT_FILENAME),
            PCS_BENCH_INGEST_FILENAME: str(ingest_path),
        },
        "failure_summary": ingest.get("failure_summary"),
        "source_repo": ingest["source_repo"],
        "source_commit": ingest["source_commit"],
        "signature_or_digest": ingest["signature_or_digest"],
    }
    legacy_path = out_dir / LEGACY_PAYLOAD_FILENAME
    legacy_path.write_text(json.dumps(legacy, indent=2) + "\n", encoding="utf-8")
    paths[LEGACY_PAYLOAD_FILENAME] = str(legacy_path)

    ingest_errors = validate_v0_reports(repo_root, {PCS_BENCH_INGEST_FILENAME: ingest})
    if ingest_errors:
        raise ValueError("; ".join(ingest_errors[:5]))
    return paths


def load_v0_reports_from_dir(out_dir: Path) -> dict[str, dict[str, Any]]:
    reports: dict[str, dict[str, Any]] = {}
    for filename in (*V0_REPORT_FILENAMES, EXPLAIN_QUALITY_REPORT_FILENAME):
        path = out_dir / filename
        if not path.is_file():
            raise FileNotFoundError(f"missing benchmark artifact: {path}")
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError(f"expected JSON object in {path}")
        reports[filename] = payload
    return reports


def validate_benchmark_output_dir(
    out_dir: Path,
    repo_root: Path,
    *,
    pcs_core_root: Path | None = None,
) -> list[str]:
    """Validate a completed PCS rendering benchmark output directory."""
    errors: list[str] = []
    out_dir = out_dir.resolve()
    required = (*V0_REPORT_FILENAMES, EXPLAIN_QUALITY_REPORT_FILENAME, PCS_BENCH_INGEST_FILENAME)
    for filename in required:
        if not (out_dir / filename).is_file():
            errors.append(f"missing {filename}")
    if errors:
        return errors
    try:
        reports = load_v0_reports_from_dir(out_dir)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        return [str(exc)]
    errors.extend(validate_v0_reports(repo_root, reports))
    ingest = json.loads((out_dir / PCS_BENCH_INGEST_FILENAME).read_text(encoding="utf-8"))
    if isinstance(ingest, dict):
        reports[PCS_BENCH_INGEST_FILENAME] = ingest
        errors.extend(validate_v0_reports(repo_root, {PCS_BENCH_INGEST_FILENAME: ingest}))
        expected_sig = canonical_hash(ingest)
        actual_sig = str(ingest.get("signature_or_digest") or "")
        if actual_sig != expected_sig:
            errors.append("pcs_bench_ingest.v0.json: signature_or_digest mismatch (recompute canonical hash)")
        suite_err = validate_suite_id(repo_root, str(ingest.get("suite_id") or ""))
        if suite_err:
            errors.append(suite_err)
        if str(ingest.get("workflow_id") or "") != PCS_WORKFLOW_ID:
            errors.append(f"pcs_bench_ingest.v0.json: workflow_id must be {PCS_WORKFLOW_ID!r}")
        for key in (
            "benchmark_runs",
            "coverage_reports",
            "explain_quality_reports",
            "query_results",
            "rendering_reports",
        ):
            if key not in ingest:
                errors.append(f"pcs_bench_ingest.v0.json: missing {key}")
    if pcs_core_root is not None:
        from sm_pipeline.benchmark.pcs_core_benchmark_validate import (
            validate_benchmark_artifacts_with_pcs_core,
        )

        errors.extend(validate_benchmark_artifacts_with_pcs_core(reports, pcs_core_root.resolve()))
    run = reports["benchmark_run.v0.json"]
    if not run.get("passed"):
        errors.extend(str(msg) for msg in (run.get("failures") or [])[:10])
    return errors
