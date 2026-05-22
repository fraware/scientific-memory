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
from sm_pipeline.benchmark.pcs_core_ingest import (
    PCS_WORKFLOW_ID as PCS_CORE_INGEST_WORKFLOW_ID,
    build_artifact_refs_for_ingest,
    build_embedded_pcs_bench_ingest,
    validate_embedded_ingest_contract,
    validate_release_grade_ingest,
    write_benchmark_run_sidecars,
    write_coverage_sidecars,
    write_explain_quality_sidecars,
    write_failure_localization_sidecars,
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
    "benchmark_run.v0.json": "benchmark/RenderingBenchmarkRun.v0.schema.json",
    "rendering_coverage_report.v0.json": "benchmark/RenderingCoverageReport.v0.schema.json",
    "query_coverage_report.v0.json": "benchmark/QueryCoverageReport.v0.schema.json",
    "failed_release_rendering_report.v0.json": "benchmark/FailedReleaseRenderingReport.v0.schema.json",
    "explain_quality_report.v0.json": "benchmark/ExplainQualityReport.v0.schema.json",
}

PCS_BENCH_INGEST_FILENAME = "pcs_bench_ingest.v0.json"
EXPLAIN_QUALITY_REPORT_FILENAME = "explain_quality_report.v0.json"
BENCH_SUITE_MANIFEST_FILENAME = "bench_suite_manifest.v0.json"
LEGACY_PAYLOAD_FILENAME = "pcs_bench_payload.json"
PCS_WORKFLOW_ID = PCS_CORE_INGEST_WORKFLOW_ID


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
        commit = proc.stdout.strip().lower()
        if len(commit) == 40 and all(ch in "0123456789abcdef" for ch in commit):
            return commit
    except (OSError, subprocess.SubprocessError):
        pass
    return "0" * 40


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
    v0_reports: dict[str, dict[str, Any]],
    case_results: list[dict[str, Any]],
    suite_id: str,
    source_commit: str,
    case_configs: dict[str, dict[str, Any]] | None = None,
    artifact_refs: list[dict[str, Any]] | None = None,
    producer_commands: list[dict[str, Any]] | None = None,
    producer_logs: list[str] | None = None,
) -> dict[str, Any]:
    """Canonical pcs-bench ingest with embedded pcs-core v0 objects."""
    return build_embedded_pcs_bench_ingest(
        suite_id=suite_id,
        source_commit=source_commit,
        benchmark_run_doc=benchmark_run,
        v0_reports=v0_reports,
        case_results=case_results,
        case_configs=case_configs,
        artifact_refs=artifact_refs,
        producer_commands=producer_commands,
        producer_logs=producer_logs,
    )


def _load_case_configs(case_results: list[dict[str, Any]], cases_path: Path | None) -> dict[str, dict[str, Any]]:
    configs: dict[str, dict[str, Any]] = {}
    if cases_path is None:
        return configs
    from sm_pipeline.benchmark.rendering import (
        CASE_CONFIG_NAME,
        EXPECTED_FAILURE,
        EXPECTED_STALENESS,
    )

    for case_dir in cases_path.iterdir() if cases_path.is_dir() else []:
        if not case_dir.is_dir():
            continue
        cfg_path = case_dir / CASE_CONFIG_NAME
        if not cfg_path.is_file():
            continue
        try:
            cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(cfg, dict):
            continue
        case_id = str(cfg.get("case_id") or case_dir.name)
        expected_path = case_dir / EXPECTED_FAILURE
        if expected_path.is_file():
            try:
                expected = json.loads(expected_path.read_text(encoding="utf-8"))
                if isinstance(expected, dict):
                    cfg["expected_failure"] = expected
                    if expected.get("failure_kind"):
                        cfg["expected_failure_code"] = str(expected["failure_kind"])
                    if expected.get("formal_focus"):
                        cfg["formal_focus"] = True
            except (OSError, json.JSONDecodeError):
                pass
        staleness_path = case_dir / EXPECTED_STALENESS
        if staleness_path.is_file():
            try:
                cfg["expected_staleness"] = json.loads(staleness_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                pass
        configs[case_id] = cfg
    failed_root = cases_path / "failed"
    if failed_root.is_dir():
        for case_dir in failed_root.iterdir():
            if not case_dir.is_dir():
                continue
            cfg_path = case_dir / CASE_CONFIG_NAME
            if not cfg_path.is_file():
                continue
            try:
                cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            if not isinstance(cfg, dict):
                continue
            case_id = str(cfg.get("case_id") or case_dir.name)
            expected_path = case_dir / EXPECTED_FAILURE
            if expected_path.is_file():
                try:
                    expected = json.loads(expected_path.read_text(encoding="utf-8"))
                    if isinstance(expected, dict):
                        cfg["expected_failure"] = expected
                        if expected.get("failure_kind"):
                            cfg["expected_failure_code"] = str(expected["failure_kind"])
                except (OSError, json.JSONDecodeError):
                    pass
            configs[case_id] = cfg
    return configs


def write_pcs_bench_artifacts(
    out_dir: Path,
    *,
    repo_root: Path,
    v0_reports: dict[str, dict[str, Any]],
    artifact_paths: dict[str, str],
    case_results: list[dict[str, Any]] | None = None,
    cases_path: Path | None = None,
) -> dict[str, str]:
    """Write pcs_bench_ingest.v0.json (canonical) and pcs_bench_payload.json (legacy alias)."""
    benchmark_run = v0_reports["benchmark_run.v0.json"]
    eq_bundle = v0_reports.get(EXPLAIN_QUALITY_REPORT_FILENAME) or {}
    suite_id = str(benchmark_run.get("suite_id") or suite_id_for_cases_path(""))
    source_commit = str(eq_bundle.get("source_commit") or resolve_source_commit(repo_root))
    cases = case_results if case_results is not None else list(benchmark_run.get("cases") or [])

    suite_err = validate_suite_id(repo_root, suite_id)
    if suite_err:
        raise ValueError(suite_err)

    ingest_path = out_dir / PCS_BENCH_INGEST_FILENAME
    existing = v0_reports.get(PCS_BENCH_INGEST_FILENAME)
    if isinstance(existing, dict):
        ingest = existing
    else:
        case_configs = _load_case_configs(cases, cases_path)
        ingest = build_pcs_bench_ingest(
            benchmark_run=benchmark_run,
            v0_reports=v0_reports,
            case_results=cases,
            suite_id=suite_id,
            source_commit=source_commit,
            case_configs=case_configs,
        )
    eq_reports = ingest.get("explain_quality_reports") or []
    if isinstance(eq_reports, list):
        write_explain_quality_sidecars(
            out_dir,
            [row for row in eq_reports if isinstance(row, dict)],
        )
    cov_reports = ingest.get("coverage_reports") or []
    if isinstance(cov_reports, list):
        write_coverage_sidecars(
            out_dir,
            [row for row in cov_reports if isinstance(row, dict)],
        )
    bench_runs = ingest.get("benchmark_runs") or []
    if isinstance(bench_runs, list) and len(bench_runs) > 1:
        write_benchmark_run_sidecars(
            out_dir,
            [row for row in bench_runs if isinstance(row, dict)],
        )
    fl_reports = ingest.get("failure_localization_reports") or []
    if isinstance(fl_reports, list) and fl_reports:
        write_failure_localization_sidecars(
            out_dir,
            [row for row in fl_reports if isinstance(row, dict)],
        )
    commit = str(ingest.get("source_commit") or "")
    if isinstance(eq_reports, list):
        ingest["artifact_refs"] = build_artifact_refs_for_ingest(
            explain_quality_reports=[row for row in eq_reports if isinstance(row, dict)],
            coverage_reports=[row for row in cov_reports if isinstance(row, dict)] if isinstance(cov_reports, list) else [],
            benchmark_runs=[row for row in bench_runs if isinstance(row, dict)] if isinstance(bench_runs, list) else [],
            failure_localization_reports=[row for row in fl_reports if isinstance(row, dict)] if isinstance(fl_reports, list) else [],
            source_commit=commit,
        )
        ingest["signature_or_digest"] = canonical_hash(
            {k: v for k, v in ingest.items() if k != "signature_or_digest"},
        )
    ingest_path.write_text(json.dumps(ingest, indent=2) + "\n", encoding="utf-8")
    paths = {PCS_BENCH_INGEST_FILENAME: str(ingest_path)}

    run_manifest = build_run_suite_manifest(
        suite_id=suite_id,
        out_dir=out_dir,
        ingest_path=ingest_path,
        passed=bool(benchmark_run.get("passed")),
        ingest=ingest,
    )
    manifest_path = out_dir / BENCH_SUITE_MANIFEST_FILENAME
    manifest_path.write_text(json.dumps(run_manifest, indent=2) + "\n", encoding="utf-8")
    paths[BENCH_SUITE_MANIFEST_FILENAME] = str(manifest_path)

    legacy = {
        "schema_version": "v0",
        "producer_id": "scientific-memory",
        "suite_id": suite_id,
        "passed": bool(benchmark_run.get("passed")),
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
        "failure_summary": benchmark_run.get("failure_summary"),
        "source_repo": ingest["source_repo"],
        "source_commit": ingest["source_commit"],
        "signature_or_digest": ingest["signature_or_digest"],
    }
    legacy_path = out_dir / LEGACY_PAYLOAD_FILENAME
    legacy_path.write_text(json.dumps(legacy, indent=2) + "\n", encoding="utf-8")
    paths[LEGACY_PAYLOAD_FILENAME] = str(legacy_path)

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
    release_grade: bool = False,
    invoke_pcs_bench_cli: bool = False,
    require_pcs_bench_cli: bool = False,
) -> list[str]:
    """Validate a completed PCS rendering benchmark output directory."""
    errors: list[str] = []
    out_dir = out_dir.resolve()
    required = (*V0_REPORT_FILENAMES, EXPLAIN_QUALITY_REPORT_FILENAME, PCS_BENCH_INGEST_FILENAME)
    for filename in required:
        if not (out_dir / filename).is_file():
            errors.append(f"missing {filename}")
    sidecar_dir = out_dir / "explain_quality_reports"
    if not sidecar_dir.is_dir():
        errors.append("missing explain_quality_reports/ (per-case ExplainQualityReport.v0 sidecars)")
    coverage_sidecar_dir = out_dir / "coverage_reports"
    if not coverage_sidecar_dir.is_dir():
        errors.append("missing coverage_reports/ (per-metric CoverageReport.v0 sidecars)")
    ingest_probe = json.loads((out_dir / PCS_BENCH_INGEST_FILENAME).read_text(encoding="utf-8"))
    if isinstance(ingest_probe, dict):
        fl_rows = ingest_probe.get("failure_localization_reports") or []
        if fl_rows and not (out_dir / "failure_localization_reports").is_dir():
            errors.append(
                "missing failure_localization_reports/ (per-case FailureLocalizationResult.v0 sidecars)",
            )
        run_rows = ingest_probe.get("benchmark_runs") or []
        if len(run_rows) > 1 and not (out_dir / "benchmark_runs").is_dir():
            errors.append("missing benchmark_runs/ (per-case BenchmarkRun.v0 sidecars)")
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
        errors.extend(validate_embedded_ingest_contract(ingest, out_dir=out_dir))
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
            "failure_localization_reports",
            "explain_quality_reports",
            "profile_coverage_reports",
            "commands",
            "logs",
        ):
            if key not in ingest:
                errors.append(f"pcs_bench_ingest.v0.json: missing {key}")
            elif not isinstance(ingest.get(key), list):
                errors.append(f"pcs_bench_ingest.v0.json: {key} must be a list")
        if ingest.get("benchmark_runs") and isinstance(ingest["benchmark_runs"][0], dict):
            first = ingest["benchmark_runs"][0]
            if "path" in first and "run_id" not in first:
                errors.append(
                    "pcs_bench_ingest.v0.json: benchmark_runs must embed BenchmarkRun.v0 objects, not path refs",
                )
    if isinstance(ingest, dict):
        from sm_pipeline.benchmark.pcs_core_benchmark_validate import _validate_pcs_bench_ingest_semantics

        errors.extend(_validate_pcs_bench_ingest_semantics(ingest))
        if release_grade:
            errors.extend(validate_release_grade_ingest(ingest, out_dir=out_dir))

    if pcs_core_root is not None:
        from sm_pipeline.benchmark.pcs_core_benchmark_validate import (
            validate_benchmark_artifacts_with_pcs_core,
        )

        errors.extend(validate_benchmark_artifacts_with_pcs_core(reports, pcs_core_root.resolve()))
    run = reports["benchmark_run.v0.json"]
    if not run.get("passed"):
        errors.extend(str(msg) for msg in (run.get("failures") or [])[:10])

    if require_pcs_bench_cli or (invoke_pcs_bench_cli and release_grade):
        from sm_pipeline.benchmark.pcs_bench_cli import require_pcs_bench_cli, run_pcs_bench_validate_ingest

        missing = require_pcs_bench_cli()
        if missing:
            errors.append(missing)
        elif pcs_core_root is not None:
            errors.extend(
                run_pcs_bench_validate_ingest(
                    out_dir / PCS_BENCH_INGEST_FILENAME,
                    pcs_core_root,
                    release_grade=release_grade,
                ),
            )
    return errors


def validate_pcs_bench_ingest_file(
    ingest_path: Path,
    repo_root: Path,
    *,
    pcs_core_root: Path | None = None,
    release_grade: bool = False,
    invoke_pcs_bench_cli: bool = False,
    require_pcs_bench_cli: bool = False,
) -> list[str]:
    """Validate a standalone pcs_bench_ingest.v0.json (contract + optional pcs-core schemas)."""
    ingest_path = ingest_path.resolve()
    out_dir = ingest_path.parent
    errors: list[str] = []
    try:
        ingest = json.loads(ingest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"{ingest_path}: {exc}"]
    if not isinstance(ingest, dict):
        return [f"{ingest_path}: expected JSON object"]

    if release_grade:
        errors.extend(validate_release_grade_ingest(ingest, out_dir=out_dir))
    else:
        errors.extend(validate_embedded_ingest_contract(ingest, out_dir=out_dir))

    expected_sig = canonical_hash(ingest)
    actual_sig = str(ingest.get("signature_or_digest") or "")
    if actual_sig != expected_sig:
        errors.append(f"{ingest_path.name}: signature_or_digest mismatch (recompute canonical hash)")

    suite_err = validate_suite_id(repo_root, str(ingest.get("suite_id") or ""))
    if suite_err:
        errors.append(suite_err)
    if str(ingest.get("workflow_id") or "") != PCS_WORKFLOW_ID:
        errors.append(f"{ingest_path.name}: workflow_id must be {PCS_WORKFLOW_ID!r}")

    from sm_pipeline.benchmark.pcs_core_benchmark_validate import _validate_pcs_bench_ingest_semantics

    errors.extend(_validate_pcs_bench_ingest_semantics(ingest))

    if pcs_core_root is not None:
        from sm_pipeline.benchmark.pcs_core_benchmark_validate import (
            validate_benchmark_artifacts_with_pcs_core,
        )

        errors.extend(
            validate_benchmark_artifacts_with_pcs_core(
                {PCS_BENCH_INGEST_FILENAME: ingest},
                pcs_core_root.resolve(),
            ),
        )
    if require_pcs_bench_cli or (invoke_pcs_bench_cli and release_grade):
        from sm_pipeline.benchmark.pcs_bench_cli import require_pcs_bench_cli, run_pcs_bench_validate_ingest

        missing = require_pcs_bench_cli()
        if missing:
            errors.append(missing)
        elif pcs_core_root is not None:
            errors.extend(
                run_pcs_bench_validate_ingest(
                    ingest_path,
                    pcs_core_root,
                    release_grade=release_grade,
                ),
            )
    return errors
