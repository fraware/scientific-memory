"""Schema and semantic validation for assurance artifacts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator
from referencing import Registry, Resource
from referencing.jsonschema import DRAFT202012

from sm_pipeline.assurance.hashing import content_digest, normalize_digest
from sm_pipeline.assurance.models import (
    ActionCalibrationRecord,
    ScientificOutcomeRecord,
)

_BASE_URI = "https://scientific-memory.org/schemas/assurance/"


class AssuranceValidationError(ValueError):
    """Fail-closed assurance validation error."""


def assurance_schema_dir(repo_root: Path) -> Path:
    return repo_root.resolve() / "schemas" / "assurance"


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def build_assurance_registry(repo_root: Path) -> Registry:
    schemas_dir = assurance_schema_dir(repo_root)
    registry = Registry()
    for path in sorted(schemas_dir.glob("*.schema.json")):
        schema = _load_json(path)
        schema_id = schema.get("$id") or f"{_BASE_URI}{path.name}"
        registry = registry.with_resource(
            schema_id,
            Resource.from_contents(schema, default_specification=DRAFT202012),
        )
        # Also register by relative filename for $ref resolution
        registry = registry.with_resource(
            path.name,
            Resource.from_contents(schema, default_specification=DRAFT202012),
        )
    return registry


def load_schema(repo_root: Path, name: str) -> dict[str, Any]:
    path = assurance_schema_dir(repo_root) / name
    if not path.is_file():
        raise AssuranceValidationError(f"Unknown assurance schema: {name}")
    schema = _load_json(path)
    if not isinstance(schema, dict):
        raise AssuranceValidationError(f"Invalid schema document: {name}")
    return schema


def validate_against_schema(repo_root: Path, schema_name: str, instance: dict[str, Any]) -> None:
    schema = load_schema(repo_root, schema_name)
    registry = build_assurance_registry(repo_root)
    validator = Draft202012Validator(schema, registry=registry)
    errors = sorted(validator.iter_errors(instance), key=lambda e: list(e.path))
    if errors:
        messages = "; ".join(f"{'/'.join(str(p) for p in e.path)}: {e.message}" for e in errors[:8])
        raise AssuranceValidationError(f"Schema {schema_name} validation failed: {messages}")


def validate_schema_version(instance: dict[str, Any]) -> None:
    version = instance.get("schema_version")
    if version != "v1":
        raise AssuranceValidationError(
            f"Unknown schema_version {version!r}; only 'v1' is supported"
        )


def validate_integrity_envelope(instance: dict[str, Any], *, envelope_key: str = "integrity") -> None:
    envelope = instance.get(envelope_key)
    if not isinstance(envelope, dict):
        raise AssuranceValidationError("Missing integrity envelope")
    declared = envelope.get("content_digest")
    if not isinstance(declared, str) or not declared:
        raise AssuranceValidationError("Missing integrity.content_digest")
    computed = content_digest(instance)
    if normalize_digest(declared) != normalize_digest(computed):
        raise AssuranceValidationError(
            f"Integrity digest mismatch: declared={declared} computed={computed}"
        )


def seal_integrity(
    instance: dict[str, Any],
    *,
    writer_identity: str,
    created_at: str,
) -> dict[str, Any]:
    """Return a copy with integrity.content_digest sealed for the payload."""
    payload = dict(instance)
    payload["integrity"] = {
        "content_digest": "sha256:" + ("0" * 64),
        "writer_identity": writer_identity,
        "schema_version": "v1",
        "created_at": created_at,
    }
    digest = content_digest(payload)
    payload["integrity"] = {
        "content_digest": digest,
        "writer_identity": writer_identity,
        "schema_version": "v1",
        "created_at": created_at,
    }
    return payload


def validate_outcome_record(repo_root: Path, data: dict[str, Any]) -> ScientificOutcomeRecord:
    validate_schema_version(data)
    validate_against_schema(repo_root, "ScientificOutcomeRecord.v1.schema.json", data)
    validate_integrity_envelope(data)
    return ScientificOutcomeRecord.model_validate(data)


def validate_calibration_record(repo_root: Path, data: dict[str, Any]) -> ActionCalibrationRecord:
    validate_schema_version(data)
    if "prediction_presence" not in data:
        raise AssuranceValidationError("prediction_presence map is required")
    validate_against_schema(repo_root, "ActionCalibrationRecord.v1.schema.json", data)
    validate_integrity_envelope(data)
    try:
        return ActionCalibrationRecord.model_validate(data)
    except Exception as exc:  # noqa: BLE001 — surface as fail-closed validation
        raise AssuranceValidationError(str(exc)) from exc


def reject_duplicate_outcome_id(existing_ids: set[str], outcome_id: str) -> None:
    if outcome_id in existing_ids:
        raise AssuranceValidationError(f"Duplicate outcome_id rejected: {outcome_id}")


def outcome_to_portal_read_model(record: ScientificOutcomeRecord | dict[str, Any]) -> dict[str, Any]:
    if isinstance(record, ScientificOutcomeRecord):
        data = record.model_dump(mode="json")
    else:
        data = dict(record)
    return {
        "schema_version": "AssuranceOutcomeReadModel.v1",
        "outcome_id": data["outcome_id"],
        "action_id": data["action_id"],
        "scientific_question_id": data["scientific_question_id"],
        "claim_ids": data.get("claim_ids") or [],
        "proposed_action_id": data["proposed_action_id"],
        "measured_result": data.get("measured_result"),
        "delayed_result_status": data.get("delayed_result_status"),
        "missing_data": data.get("missing_data"),
        "replication_status": data.get("replication_status"),
        "adverse_events": data.get("adverse_events") or [],
        "evidence_classes": data.get("evidence_classes") or [],
        "privacy": data.get("privacy") or "public",
        "reviewer_assessment": data.get("reviewer_assessment"),
        "non_claim": "Presence of this record does not constitute claim acceptance.",
    }


def calibration_to_portal_read_model(record: ActionCalibrationRecord | dict[str, Any]) -> dict[str, Any]:
    if isinstance(record, ActionCalibrationRecord):
        data = record.model_dump(mode="json")
    else:
        data = dict(record)
    return {
        "schema_version": "AssuranceCalibrationReadModel.v1",
        "calibration_id": data["calibration_id"],
        "action_id": data["action_id"],
        "prediction_presence": data.get("prediction_presence"),
        "predicted_success": data.get("predicted_success"),
        "predicted_information_gain": data.get("predicted_information_gain"),
        "predicted_cost": data.get("predicted_cost"),
        "predicted_time": data.get("predicted_time"),
        "predicted_risk": data.get("predicted_risk"),
        "realized_outcome_id": data.get("realized_outcome_id"),
        "calibration_class": data.get("calibration_class"),
        "aggregation_eligibility": data.get("aggregation_eligibility"),
        "missingness": data.get("missingness"),
        "privacy": data.get("privacy") or "public",
        "non_claim": "Calibration does not rewrite claim status.",
    }
