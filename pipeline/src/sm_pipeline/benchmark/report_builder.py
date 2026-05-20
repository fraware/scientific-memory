"""Split PCS rendering benchmark results into v0 report artifacts for pcs-bench."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

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
}

PCS_BENCH_INGEST_FILENAME = "pcs_bench_ingest.v0.json"
LEGACY_PAYLOAD_FILENAME = "pcs_bench_payload.json"


def _now() -> str:
    return datetime.now(UTC).isoformat()


def build_v0_reports(
    case_results: list[dict[str, Any]],
    *,
    repo_root: Path,
    cases_path: Path,
    aggregate_failures: list[str],
    metrics: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    """Build the four pcs-bench-facing report documents."""
    success_cases = [c for c in case_results if not c.get("failure_mode")]
    failed_cases = [c for c in case_results if c.get("failure_mode")]

    rendering_cases = []
    for result in case_results:
        if result.get("failure_mode"):
            continue
        rendering_cases.append(
            {
                "case_id": result.get("case_id"),
                "claim_id": result.get("claim_id"),
                "release_id": result.get("release_id"),
                "passed": result.get("passed"),
                "failures": result.get("failures") or [],
                "section_coverage": result.get("section_coverage") or {},
                "render_metrics": {
                    k: v
                    for k, v in (result.get("metrics") or {}).items()
                    if k not in ("query_responses_correct", "release_comparison_correct", "failure_evidence_rendered")
                },
            },
        )

    query_cases = []
    for result in case_results:
        queries = result.get("queries") or {}
        query_cases.append(
            {
                "case_id": result.get("case_id"),
                "passed": queries.get("passed", result.get("passed")),
                "queries": queries.get("queries") or [],
                "compare": result.get("compare") if not result.get("compare", {}).get("skipped") else None,
            },
        )

    failed_rendering_cases = []
    for result in case_results:
        if not result.get("failure_mode"):
            continue
        failed_rendering_cases.append(
            {
                "case_id": result.get("case_id"),
                "claim_id": result.get("claim_id"),
                "passed": result.get("passed"),
                "failures": result.get("failures") or [],
                "failure_evidence": result.get("failure_evidence") or {},
            },
        )

    benchmark_run = {
        "schema_version": "BenchmarkRun.v0",
        "benchmark_id": "pcs_rendering",
        "generated_at": _now(),
        "repo_root": str(repo_root.resolve()),
        "cases_path": str(cases_path.resolve()),
        "passed": not aggregate_failures,
        "case_count": len(case_results),
        "failures": aggregate_failures,
        "metrics": metrics,
        "pcs_bench": {
            "consumer": "pcs-bench",
            "ingest_files": list(V0_SCHEMAS.keys()),
            "metric_keys": list(metrics.keys()),
        },
        "cases": [
            {
                "case_id": c.get("case_id"),
                "claim_id": c.get("claim_id"),
                "release_id": c.get("release_id"),
                "passed": c.get("passed"),
                "failures": c.get("failures") or [],
                "failure_mode": bool(c.get("failure_mode")),
            }
            for c in case_results
        ],
    }

    rendering_report = {
        "schema_version": "RenderingCoverageReport.v0",
        "generated_at": _now(),
        "passed": all(c.get("passed") for c in rendering_cases) if rendering_cases else True,
        "case_count": len(rendering_cases),
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

    return {
        "benchmark_run.v0.json": benchmark_run,
        "rendering_coverage_report.v0.json": rendering_report,
        "query_coverage_report.v0.json": query_report,
        "failed_release_rendering_report.v0.json": failed_report,
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
        for err in sorted(validator.iter_errors(payload), key=lambda item: item.path):
            path = "/".join(str(p) for p in err.path) or "(root)"
            errors.append(f"{filename}: {path}: {err.message}")
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
    benchmark_run: dict[str, Any],
    *,
    out_dir: Path,
    artifact_paths: dict[str, str],
) -> dict[str, Any]:
    """Single manifest pcs-bench reads to locate all v0 report artifacts."""
    metrics = dict(benchmark_run.get("metrics") or {})
    pcs_meta = benchmark_run.get("pcs_bench") if isinstance(benchmark_run.get("pcs_bench"), dict) else {}
    ingest_files = list(pcs_meta.get("ingest_files") or V0_REPORT_FILENAMES)
    artifacts = {name: artifact_paths.get(name) or str((out_dir / name).resolve()) for name in ingest_files}
    return {
        "schema_version": "PcsBenchIngest.v0",
        "benchmark_id": str(benchmark_run.get("benchmark_id") or "pcs_rendering"),
        "consumer": "pcs-bench",
        "passed": bool(benchmark_run.get("passed")),
        "generated_at": str(benchmark_run.get("generated_at") or _now()),
        "case_count": int(benchmark_run.get("case_count") or 0),
        "metrics": metrics,
        "failures": list(benchmark_run.get("failures") or []),
        "ingest_files": ingest_files,
        "artifacts": artifacts,
        "metric_keys": list(pcs_meta.get("metric_keys") or metrics.keys()),
    }


def write_pcs_bench_artifacts(
    out_dir: Path,
    *,
    repo_root: Path,
    v0_reports: dict[str, dict[str, Any]],
    artifact_paths: dict[str, str],
) -> dict[str, str]:
    """Write pcs_bench_ingest.v0.json (canonical) and pcs_bench_payload.json (legacy alias)."""
    benchmark_run = v0_reports["benchmark_run.v0.json"]
    ingest = build_pcs_bench_ingest(benchmark_run, out_dir=out_dir, artifact_paths=artifact_paths)
    ingest_path = out_dir / PCS_BENCH_INGEST_FILENAME
    ingest_path.write_text(json.dumps(ingest, indent=2) + "\n", encoding="utf-8")
    paths = {PCS_BENCH_INGEST_FILENAME: str(ingest_path)}

    legacy = {
        "benchmark": ingest["benchmark_id"],
        "schema_version": ingest["schema_version"],
        "passed": ingest["passed"],
        "case_count": ingest["case_count"],
        "generated_at": ingest["generated_at"],
        "metrics": ingest["metrics"],
        "failures": ingest["failures"],
        "ingest_manifest": PCS_BENCH_INGEST_FILENAME,
        "artifacts": ingest["artifacts"],
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
    for filename in V0_REPORT_FILENAMES:
        path = out_dir / filename
        if not path.is_file():
            raise FileNotFoundError(f"missing benchmark artifact: {path}")
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError(f"expected JSON object in {path}")
        reports[filename] = payload
    return reports


def validate_benchmark_output_dir(out_dir: Path, repo_root: Path) -> list[str]:
    """Validate a completed PCS rendering benchmark output directory."""
    errors: list[str] = []
    out_dir = out_dir.resolve()
    for filename in (*V0_REPORT_FILENAMES, PCS_BENCH_INGEST_FILENAME):
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
        errors.extend(validate_v0_reports(repo_root, {PCS_BENCH_INGEST_FILENAME: ingest}))
    run = reports["benchmark_run.v0.json"]
    if not run.get("passed"):
        errors.extend(str(msg) for msg in (run.get("failures") or [])[:10])
    return errors
