"""Validate signed PCS bundles: pcs-core (canonical) + legacy mirrors."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator
from referencing import Registry, Resource
from referencing.jsonschema import DRAFT202012

from sm_pipeline.pcs_validate.bundle_detection import (
    detect_bundle_shape,
    get_science_claim_bundle,
    is_legacy_signed_bundle,
    is_pcs_core_signed_bundle,
)
from sm_pipeline.pcs_validate.bundle_semantics import (
    collect_semantic_errors,
    collect_semantic_warnings,
    verification_result_passed,
)
from sm_pipeline.pcs_validate.pcs_core_hook import pcs_core_available, validate_with_pcs_core
from sm_pipeline.pcs_validate.schema_registry import (
    LEGACY_SCIENCE_CLAIM_BUNDLE_SCHEMA,
    LEGACY_SIGNED_BUNDLE_SCHEMA,
    LEGACY_VERIFICATION_RESULT_SCHEMA,
    SCHEMA_ALIASES,
    resolve_schema_path,
)


class BundleValidationError(ValueError):
    """Raised when a PCS bundle fails validation."""


LEGACY_STRICT_MESSAGE = (
    "Legacy LabTrust signed bundle requires --allow-legacy in strict mode"
)
UNRECOGNIZED_SHAPE_MESSAGE = (
    "Unrecognized signed bundle shape; expected PCS Core SignedScienceClaimBundle.v0"
)


def _repo_root_from_here() -> Path:
    return Path(__file__).resolve().parents[4]


def _pcs_schemas_dir(repo_root: Path | None = None) -> Path:
    root = repo_root or _repo_root_from_here()
    return root / "schemas" / "pcs"


def _load_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def _build_pcs_registry(repo_root: Path) -> Registry:
    registry = Registry()
    schemas_dir = _pcs_schemas_dir(repo_root)
    skip = set(SCHEMA_ALIASES.keys())
    paths = list(schemas_dir.glob("*.json")) + list(schemas_dir.glob("legacy/*.json"))
    for path in sorted(paths):
        if path.name in skip:
            continue
        schema = _load_json(path)
        schema_id = schema.get("$id")
        if not isinstance(schema_id, str):
            continue
        registry = registry.with_resource(
            schema_id,
            Resource.from_contents(schema, default_specification=DRAFT202012),
        )
    return registry


def validator_for(schema_name: str, repo_root: Path) -> Draft202012Validator:
    schema_path = resolve_schema_path(_pcs_schemas_dir(repo_root), schema_name)
    schema = _load_json(schema_path)
    registry = _build_pcs_registry(repo_root)
    return Draft202012Validator(schema, registry=registry)


def _get_verification_result(bundle: dict[str, Any], scb: dict[str, Any] | None) -> dict[str, Any] | None:
    vr = bundle.get("verification_result")
    if isinstance(vr, dict):
        return vr
    if scb is not None:
        nested = scb.get("verification_result")
        if isinstance(nested, dict):
            return nested
    return None


def _validate_legacy_bundle(bundle: dict[str, Any], repo_root: Path) -> list[str]:
    """LabTrust portal legacy envelopes use schemas/pcs/legacy/* mirrors."""
    errors: list[str] = []
    signed_validator = validator_for(LEGACY_SIGNED_BUNDLE_SCHEMA, repo_root)
    for err in sorted(signed_validator.iter_errors(bundle), key=lambda e: e.path):
        errors.append(err.message)

    scb = get_science_claim_bundle(bundle)
    if scb is None:
        errors.append("science_claim_bundle is required")
    else:
        scb_validator = validator_for(LEGACY_SCIENCE_CLAIM_BUNDLE_SCHEMA, repo_root)
        for err in sorted(scb_validator.iter_errors(scb), key=lambda e: e.path):
            errors.append(f"science_claim_bundle: {err.message}")

    vr = _get_verification_result(bundle, scb)
    if isinstance(vr, dict):
        vr_validator = validator_for(LEGACY_VERIFICATION_RESULT_SCHEMA, repo_root)
        for err in sorted(vr_validator.iter_errors(vr), key=lambda e: e.path):
            errors.append(f"verification_result: {err.message}")

    return errors


def validate_signed_bundle(
    bundle: dict[str, Any],
    *,
    repo_root: Path | None = None,
    strict: bool = True,
    allow_legacy: bool = False,
) -> list[str]:
    """
    Validate a signed science claim bundle.

    Strict mode (default): PCS Core signed bundles are accepted; legacy LabTrust
    envelopes require ``allow_legacy=True`` or ``strict=False``. Semantic import
    rules (passed verification, non-empty assumptions, provenance) always apply
    when ``strict=True``.
    """
    root = (repo_root or _repo_root_from_here()).resolve()
    shape = detect_bundle_shape(bundle)
    errors: list[str] = []

    if shape == "legacy":
        if strict and not allow_legacy:
            raise BundleValidationError(LEGACY_STRICT_MESSAGE)
        errors.extend(_validate_legacy_bundle(bundle, root))
    elif shape == "pcs_core":
        if pcs_core_available():
            errors.extend(validate_with_pcs_core(bundle))
        else:
            errors.append(
                "pcs-core SignedScienceClaimBundle requires the pcs-core package "
                "(uv sync --project pipeline --extra pcs when pcs-core is present)"
            )
    else:
        raise BundleValidationError(UNRECOGNIZED_SHAPE_MESSAGE)

    errors.extend(collect_semantic_errors(bundle, strict=strict))

    if errors and strict:
        raise BundleValidationError("; ".join(errors))

    if strict:
        return collect_semantic_warnings(bundle)

    warnings = collect_semantic_warnings(bundle)
    scb = get_science_claim_bundle(bundle)
    vr = _get_verification_result(bundle, scb)
    if vr is None:
        warnings.append(
            "VerificationResult is absent; import proceeds with advisory only."
        )
    return warnings


def verification_status_label(bundle: dict[str, Any]) -> str:
    """Summary status for scientific_memory_import_report.json."""
    scb = get_science_claim_bundle(bundle)
    vr = _get_verification_result(bundle, scb)
    if vr is None:
        return "absent"
    if verification_result_passed(vr):
        return "passed"
    return "failed"
