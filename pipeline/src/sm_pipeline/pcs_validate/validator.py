"""Validate signed PCS bundles (pcs-core hook + vendored JSON Schema)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator
from referencing import Registry, Resource
from referencing.jsonschema import DRAFT202012

from sm_pipeline.pcs_validate.pcs_core_hook import (
    is_pcs_core_science_claim_bundle,
    is_pcs_core_verification_result,
    validate_with_pcs_core,
)

PCS_SCHEMA_BASE_URI = "https://scientific-memory.org/schemas/pcs/"


class BundleValidationError(ValueError):
    """Raised when a PCS bundle fails validation."""


def _repo_root_from_here() -> Path:
    return Path(__file__).resolve().parents[4]


def _pcs_schemas_dir(repo_root: Path | None = None) -> Path:
    root = repo_root or _repo_root_from_here()
    return root / "schemas" / "pcs"


def _load_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def _build_pcs_registry(repo_root: Path) -> Registry:
    registry = Registry()
    for path in sorted(_pcs_schemas_dir(repo_root).glob("*.json")):
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
    schema_path = _pcs_schemas_dir(repo_root) / schema_name
    schema = _load_json(schema_path)
    registry = _build_pcs_registry(repo_root)
    return Draft202012Validator(schema, registry=registry)


def validate_signed_bundle(
    bundle: dict[str, Any],
    *,
    repo_root: Path | None = None,
    strict: bool = True,
) -> list[str]:
    """
    Validate a signed science claim bundle.

    Returns import warnings (non-fatal). Raises BundleValidationError when strict
    and validation fails.
    """
    root = (repo_root or _repo_root_from_here()).resolve()
    errors: list[str] = []

    if strict:
        errors.extend(validate_with_pcs_core(bundle))

    validator = validator_for("signed_science_claim_bundle.schema.json", root)
    for err in sorted(validator.iter_errors(bundle), key=lambda e: e.path):
        errors.append(err.message)

    scb = bundle.get("science_claim_bundle")
    if isinstance(scb, dict) and not is_pcs_core_science_claim_bundle(scb):
        scb_validator = validator_for("science_claim_bundle.schema.json", root)
        for err in sorted(scb_validator.iter_errors(scb), key=lambda e: e.path):
            errors.append(f"science_claim_bundle: {err.message}")

        assumption_set = scb.get("assumption_set")
        assumptions = (
            assumption_set.get("assumptions")
            if isinstance(assumption_set, dict)
            else None
        )
        if not assumptions:
            errors.append("science_claim_bundle.assumption_set.assumptions is required")

    if isinstance(scb, dict) and is_pcs_core_science_claim_bundle(scb):
        assumption_set = scb.get("assumption_set")
        assumptions = (
            assumption_set.get("assumptions")
            if isinstance(assumption_set, dict)
            else None
        )
        if not assumptions:
            errors.append("science_claim_bundle.assumption_set.assumptions is required")

    vr = bundle.get("verification_result")
    if vr is None and isinstance(scb, dict):
        vr = scb.get("verification_result")
    if isinstance(vr, dict) and not is_pcs_core_verification_result(vr):
        vr_validator = validator_for("verification_result.schema.json", root)
        for err in sorted(vr_validator.iter_errors(vr), key=lambda e: e.path):
            errors.append(f"verification_result: {err.message}")

    if errors and strict:
        raise BundleValidationError("; ".join(errors))

    return collect_import_warnings(bundle) if not errors else []


def collect_import_warnings(bundle: dict[str, Any]) -> list[str]:
    """Non-fatal warnings required by the PCS import contract."""
    warnings: list[str] = []
    scb = bundle.get("science_claim_bundle")
    if not isinstance(scb, dict):
        return warnings

    vr = bundle.get("verification_result")
    if vr is None:
        vr = scb.get("verification_result")
    if vr is None:
        warnings.append("VerificationResult is absent; import proceeds with advisory only.")

    trace_cert = scb.get("trace_certificate")
    if not isinstance(trace_cert, dict):
        certificates = scb.get("certificates")
        if isinstance(certificates, list) and certificates and isinstance(certificates[0], dict):
            trace_cert = certificates[0]
    if isinstance(trace_cert, dict):
        status = str(trace_cert.get("status") or "")
        if status != "CertificateChecked":
            warnings.append(
                f"trace_certificate.status is {status!r}, expected CertificateChecked."
            )

    return warnings
