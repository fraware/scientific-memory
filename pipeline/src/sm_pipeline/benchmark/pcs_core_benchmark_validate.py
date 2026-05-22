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
# pcs-core validates canonical ingest and embedded artifacts; SM companion dialect reports use SM mirrors only.
PCS_CORE_OUTPUT_ARTIFACT_TYPES: dict[str, tuple[str, ...]] = {
    EXPLAIN_QUALITY_REPORT_FILENAME: ("ExplainQualityReport.v0",),
    PCS_BENCH_INGEST_FILENAME: ("PcsBenchIngest.v0",),
}

# SM mirror validation (validate_benchmark_reports_dual / validate_v0_reports).
SM_MIRROR_ARTIFACT_TYPES: dict[str, tuple[str, ...]] = {
    "rendering_coverage_report.v0.json": ("RenderingCoverageReport.v0",),
    "query_coverage_report.v0.json": ("QueryCoverageReport.v0",),
    "failed_release_rendering_report.v0.json": ("FailedReleaseRenderingReport.v0",),
    EXPLAIN_QUALITY_REPORT_FILENAME: ("ExplainQualityReport.v0",),
}

INGEST_EMBEDDED_TYPES: dict[str, str] = {
    "benchmark_runs": "BenchmarkRun.v0",
    "coverage_reports": "CoverageReport.v0",
    "failure_localization_reports": "FailureLocalizationResult.v0",
    "explain_quality_reports": "ExplainQualityReport.v0",
    "profile_coverage_reports": "ProfileCoverageReport.v0",
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

    common_path = schemas_dir / "common.defs.json"
    if common_path.is_file():
        try:
            common_schema = _load_schema(common_path)
            common_resource = Resource.from_contents(
                common_schema,
                default_specification=DRAFT202012,
            )
            common_id = common_schema.get("$id")
            if isinstance(common_id, str):
                registry = registry.with_resource(common_id, common_resource)
            registry = registry.with_resource("common.defs.json", common_resource)
        except (OSError, json.JSONDecodeError, ValueError):
            pass

    paths = list(schemas_dir.rglob("*.schema.json"))
    for path in sorted(paths):
        try:
            schema = _load_schema(path)
        except (OSError, json.JSONDecodeError, ValueError):
            continue
        resource = Resource.from_contents(schema, default_specification=DRAFT202012)
        schema_id = schema.get("$id")
        if isinstance(schema_id, str):
            registry = registry.with_resource(schema_id, resource)
        registry = registry.with_resource(path.name, resource)
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

    ingest_payload = reports.get(PCS_BENCH_INGEST_FILENAME)
    if isinstance(ingest_payload, dict):
        ingest_schema_path: Path | None = None
        for candidate_type in PCS_CORE_OUTPUT_ARTIFACT_TYPES[PCS_BENCH_INGEST_FILENAME]:
            for path in _schema_file_candidates(pcs_core_root, candidate_type):
                if path.is_file():
                    ingest_schema_path = path
                    break
            if ingest_schema_path:
                break
        if ingest_schema_path is None:
            errors.append(
                f"{PCS_BENCH_INGEST_FILENAME}: no pcs-core schema for PcsBenchIngest.v0 under {pcs_core_root / 'schemas'}",
            )
        else:
            errors.extend(
                _validate_with_schema_file(
                    ingest_payload,
                    ingest_schema_path,
                    registry,
                    label=PCS_BENCH_INGEST_FILENAME,
                ),
            )
            for array_key, artifact_type in INGEST_EMBEDDED_TYPES.items():
                rows = ingest_payload.get(array_key)
                if not isinstance(rows, list):
                    continue
                for index, row in enumerate(rows):
                    if not isinstance(row, dict):
                        errors.append(f"{PCS_BENCH_INGEST_FILENAME}/{array_key}[{index}]: expected object")
                        continue
                    schema_path: Path | None = None
                    for path in _schema_file_candidates(pcs_core_root, artifact_type):
                        if path.is_file():
                            schema_path = path
                            break
                    if schema_path is None:
                        errors.append(
                            f"{PCS_BENCH_INGEST_FILENAME}/{array_key}[{index}]: "
                            f"no pcs-core schema for {artifact_type}",
                        )
                        continue
                    label = f"{PCS_BENCH_INGEST_FILENAME}/{array_key}/{row.get('case_id', row.get('coverage_id', index))}"
                    errors.extend(
                        _validate_with_schema_file(row, schema_path, registry, label=label),
                    )
            refs = ingest_payload.get("artifact_refs")
            if isinstance(refs, list):
                ref_schema_path: Path | None = None
                for path in _schema_file_candidates(pcs_core_root, "BenchmarkArtifactRef.v0"):
                    if path.is_file():
                        ref_schema_path = path
                        break
                if ref_schema_path is None:
                    errors.append(
                        f"{PCS_BENCH_INGEST_FILENAME}: no pcs-core schema for BenchmarkArtifactRef.v0",
                    )
                else:
                    for index, ref in enumerate(refs):
                        if not isinstance(ref, dict):
                            errors.append(f"{PCS_BENCH_INGEST_FILENAME}/artifact_refs[{index}]: expected object")
                            continue
                        label = f"{PCS_BENCH_INGEST_FILENAME}/artifact_refs/{ref.get('path', index)}"
                        errors.extend(
                            _validate_with_schema_file(ref, ref_schema_path, registry, label=label),
                        )

    for filename, artifact_types in PCS_CORE_OUTPUT_ARTIFACT_TYPES.items():
        if filename == PCS_BENCH_INGEST_FILENAME:
            continue
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

    ingest_payload = reports.get(PCS_BENCH_INGEST_FILENAME)
    if isinstance(ingest_payload, dict):
        errors.extend(_validate_pcs_bench_ingest_semantics(ingest_payload))

    if PCS_BENCH_INGEST_FILENAME not in reports:
        return [f"pcs-core validation: missing {PCS_BENCH_INGEST_FILENAME}"]
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


def _validate_pcs_bench_ingest_semantics(ingest: dict[str, Any]) -> list[str]:
    """pcs-core semantic rules (artifact_refs vs embedded digests, producer contract)."""
    from sm_pipeline.pcs_validate.pcs_core_hook import pcs_core_available, validate_protocol_artifact

    if not pcs_core_available():
        return _validate_pcs_bench_ingest_semantics_local(ingest)
    return validate_protocol_artifact(ingest, "PcsBenchIngest.v0")


def _validate_pcs_bench_ingest_semantics_local(ingest: dict[str, Any]) -> list[str]:
    """Minimal mirror of pcs-core ingest semantics when pcs_core package is not installed."""
    errors: list[str] = []
    explain_rows = ingest.get("explain_quality_reports")
    coverage_rows = ingest.get("coverage_reports")
    refs = ingest.get("artifact_refs")
    has_embedded = (
        (isinstance(explain_rows, list) and explain_rows)
        or (isinstance(coverage_rows, list) and coverage_rows)
    )
    if has_embedded and refs is None:
        errors.append(
            "PcsBenchIngest.v0 producer 'scientific-memory' requires artifact_refs "
            "when explain_quality_reports or coverage_reports are embedded",
        )
        return errors
    if not isinstance(refs, list):
        return errors
    ref_keys = {
        (str(ref.get("artifact_type")), str(ref.get("sha256")))
        for ref in refs
        if isinstance(ref, dict)
    }
    paths = [str(ref.get("path")) for ref in refs if isinstance(ref, dict) and ref.get("path")]
    if len(paths) != len(set(paths)):
        errors.append("PcsBenchIngest.v0 artifact_refs contains duplicate path values")
    for index, row in enumerate(explain_rows or []):
        if not isinstance(row, dict):
            continue
        digest = row.get("signature_or_digest")
        if isinstance(digest, str) and ("ExplainQualityReport.v0", digest) not in ref_keys:
            errors.append(
                f"explain_quality_reports[{index}]: missing artifact_refs entry for digest {digest}",
            )
    for index, row in enumerate(coverage_rows or []):
        if not isinstance(row, dict):
            continue
        digest = row.get("signature_or_digest")
        if isinstance(digest, str) and ("CoverageReport.v0", digest) not in ref_keys:
            errors.append(
                f"coverage_reports[{index}]: missing artifact_refs entry for digest {digest}",
            )
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
    elif reports.get(PCS_BENCH_INGEST_FILENAME):
        ingest = reports[PCS_BENCH_INGEST_FILENAME]
        if isinstance(ingest, dict):
            errors.extend(_validate_pcs_bench_ingest_semantics(ingest))
    return errors
