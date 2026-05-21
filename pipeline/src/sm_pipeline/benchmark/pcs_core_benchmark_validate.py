"""Validate PCS rendering benchmark v0 outputs against pcs-core canonical schemas."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator
from referencing import Registry, Resource
from referencing.jsonschema import DRAFT202012

from sm_pipeline.benchmark.report_builder import (
    EXPLAIN_QUALITY_REPORT_FILENAME,
    PCS_BENCH_INGEST_FILENAME,
    validate_v0_reports,
)
# pcs_core package validate_artifact targets protocol artifacts, not SM rendering benchmark reports.

# Output filename -> pcs-core artifact type(s), most specific first.
OUTPUT_ARTIFACT_TYPES: dict[str, tuple[str, ...]] = {
    "benchmark_run.v0.json": ("BenchmarkRun.v0",),
    "rendering_coverage_report.v0.json": (
        "RenderingCoverageReport.v0",
        "CoverageReport.v0",
    ),
    "query_coverage_report.v0.json": (
        "QueryCoverageReport.v0",
        "CoverageReport.v0",
    ),
    "failed_release_rendering_report.v0.json": ("FailedReleaseRenderingReport.v0",),
    EXPLAIN_QUALITY_REPORT_FILENAME: ("ExplainQualityReport.v0",),
    PCS_BENCH_INGEST_FILENAME: ("PcsBenchIngest.v0",),
}

_SCHEMA_SUFFIX = ".schema.json"


def _is_pcs_core_root(path: Path) -> bool:
    resolved = path.resolve()
    return (resolved / "schemas").is_dir() or (resolved / "pyproject.toml").is_file()


def resolve_pcs_core_root(
    explicit: str | Path | None,
    *,
    repo_root: Path,
    search_siblings: bool = True,
) -> Path | None:
    """Resolve pcs-core checkout: CLI path, PCS_CORE_PATH/PCS_CORE_ROOT, sibling, or child."""
    candidates: list[Path] = []
    if explicit:
        candidates.append(Path(explicit))
    for env_key in ("PCS_CORE_PATH", "PCS_CORE_ROOT"):
        env = os.environ.get(env_key, "").strip()
        if env:
            candidates.append(Path(env))
    if search_siblings:
        root = repo_root.resolve()
        candidates.extend([root.parent / "pcs-core", root / "pcs-core"])
    for path in candidates:
        if _is_pcs_core_root(path):
            return path.resolve()
    return None


def resolve_pcs_core_from_env(*, repo_root: Path) -> Path | None:
    """Resolve pcs-core from PCS_CORE_PATH / PCS_CORE_ROOT only (no sibling search)."""
    return resolve_pcs_core_root(None, repo_root=repo_root, search_siblings=False)


def _schema_file_candidates(pcs_core_root: Path, artifact_type: str) -> list[Path]:
    base = artifact_type.removesuffix(_SCHEMA_SUFFIX)
    filename = base if base.endswith(".v0") else f"{base}.v0"
    if not filename.endswith(_SCHEMA_SUFFIX):
        filename = f"{filename}{_SCHEMA_SUFFIX}"
    return [
        pcs_core_root / "schemas" / filename,
        pcs_core_root / "schemas" / "benchmark" / filename,
        pcs_core_root / "schemas" / "pcs" / "benchmark" / filename,
        pcs_core_root / "schemas" / "pcs" / filename,
    ]


def _load_schema(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"expected JSON object schema: {path}")
    return data


def _build_registry(pcs_core_root: Path) -> Registry:
    registry = Registry()
    schemas_dir = pcs_core_root / "schemas"
    if not schemas_dir.is_dir():
        return registry
    paths = list(schemas_dir.rglob("*.schema.json"))
    for path in sorted(paths):
        try:
            schema = _load_schema(path)
        except (OSError, json.JSONDecodeError, ValueError):
            continue
        schema_id = schema.get("$id")
        if not isinstance(schema_id, str):
            continue
        registry = registry.with_resource(
            schema_id,
            Resource.from_contents(schema, default_specification=DRAFT202012),
        )
    return registry


def _validator_for_schema(schema: dict[str, Any], registry: Registry) -> Draft202012Validator:
    resource = Resource.from_contents(schema, default_specification=DRAFT202012)
    if "$id" in schema:
        return Draft202012Validator(schema, registry=registry.with_resource(schema["$id"], resource))
    return Draft202012Validator(schema, registry=registry.with_resource("urn:local", resource))


def _validate_with_schema_file(
    payload: dict[str, Any],
    schema_path: Path,
    registry: Registry,
    *,
    label: str,
) -> list[str]:
    schema = _load_schema(schema_path)
    validator = _validator_for_schema(schema, registry)
    errors: list[str] = []
    for err in sorted(validator.iter_errors(payload), key=lambda item: item.path):
        path = "/".join(str(p) for p in err.path) or "(root)"
        errors.append(f"{label}: {path}: {err.message} ({schema_path.name})")
    return errors


def validate_benchmark_artifacts_with_pcs_core(
    reports: dict[str, dict[str, Any]],
    pcs_core_root: Path,
) -> list[str]:
    """Validate benchmark report payloads using pcs-core schema files and optional pcs_core package."""
    pcs_core_root = pcs_core_root.resolve()
    if not pcs_core_root.is_dir():
        return [f"pcs-core root not found: {pcs_core_root}"]

    registry = _build_registry(pcs_core_root)
    errors: list[str] = []
    resolved_types: dict[str, str] = {}

    for filename, artifact_types in OUTPUT_ARTIFACT_TYPES.items():
        payload = reports.get(filename)
        if not isinstance(payload, dict):
            continue

        targets: list[tuple[str, dict[str, Any]]] = [(filename, payload)]
        if filename == EXPLAIN_QUALITY_REPORT_FILENAME:
            targets = [
                (f"{filename}/{row.get('report_id', row.get('case_id', 'case'))}", row)
                for row in (payload.get("reports") or [])
                if isinstance(row, dict)
            ]

        for label, target in targets:
            schema_path: Path | None = None
            artifact_type = ""
            for candidate_type in artifact_types:
                for path in _schema_file_candidates(pcs_core_root, candidate_type):
                    if path.is_file():
                        schema_path = path
                        artifact_type = candidate_type
                        break
                if schema_path:
                    break

            if schema_path is None:
                errors.append(
                    f"{label}: no pcs-core schema for {artifact_types[0]} under {pcs_core_root / 'schemas'}",
                )
                continue

            resolved_types[filename] = artifact_type
            errors.extend(_validate_with_schema_file(target, schema_path, registry, label=label))

    if errors:
        return errors

    missing = [name for name in OUTPUT_ARTIFACT_TYPES if name not in reports]
    if missing:
        return [f"pcs-core validation: missing reports: {', '.join(missing)}"]
    return []


def validate_benchmark_output_dir_with_pcs_core(
    out_dir: Path,
    pcs_core_root: Path,
    repo_root: Path,
) -> list[str]:
    """SM schema validation plus pcs-core canonical schema validation."""
    from sm_pipeline.benchmark.report_builder import load_v0_reports_from_dir, validate_benchmark_output_dir

    errors = validate_benchmark_output_dir(out_dir, repo_root)
    if errors:
        return errors

    try:
        reports = load_v0_reports_from_dir(out_dir)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        return [str(exc)]

    # Re-validate ingest explicitly (included in load set).
    ingest_path = out_dir / PCS_BENCH_INGEST_FILENAME
    if ingest_path.is_file():
        ingest = json.loads(ingest_path.read_text(encoding="utf-8"))
        if isinstance(ingest, dict):
            reports[PCS_BENCH_INGEST_FILENAME] = ingest

    errors.extend(validate_benchmark_artifacts_with_pcs_core(reports, pcs_core_root))
    return errors


def validate_benchmark_reports_dual(
    reports: dict[str, dict[str, Any]],
    *,
    repo_root: Path,
    pcs_core_root: Path | None,
) -> list[str]:
    """Validate against SM mirrors; optionally enforce pcs-core schemas when root is provided."""
    errors = validate_v0_reports(repo_root, reports)
    if pcs_core_root is not None:
        errors.extend(validate_benchmark_artifacts_with_pcs_core(reports, pcs_core_root))
    return errors
