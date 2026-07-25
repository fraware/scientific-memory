"""Validate assurance schemas and corpus/assurance action stores (fail-closed)."""

from __future__ import annotations

import json
from pathlib import Path

from sm_pipeline.assurance.graph import actions_root, load_chain, validate_chain
from sm_pipeline.assurance.hashing import file_sha256, normalize_digest
from sm_pipeline.assurance.validate import (
    AssuranceValidationError,
    validate_against_schema,
    validate_calibration_record,
    validate_outcome_record,
    validate_schema_version,
)

REQUIRED_ASSURANCE_SCHEMAS = (
    "common.defs.v1.schema.json",
    "ScientificOutcomeRecord.v1.schema.json",
    "ActionCalibrationRecord.v1.schema.json",
    "ActionChainNode.v1.schema.json",
    "ActionChainEdge.v1.schema.json",
    "AssuranceReleaseManifest.v1.schema.json",
    "ExternalArtifactRef.v1.schema.json",
    "AutonomousScienceMetrics.v1.schema.json",
)


def _read_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_assurance_schema_registry(repo_root: Path) -> None:
    """Ensure required assurance schema files exist and are loadable JSON Schema objects."""
    schemas_dir = repo_root.resolve() / "schemas" / "assurance"
    if not schemas_dir.is_dir():
        raise AssuranceValidationError("Missing schemas/assurance directory")
    for name in REQUIRED_ASSURANCE_SCHEMAS:
        path = schemas_dir / name
        if not path.is_file():
            raise AssuranceValidationError(f"Missing assurance schema: {name}")
        raw = _read_json(path)
        if not isinstance(raw, dict) or "$schema" not in raw:
            raise AssuranceValidationError(f"Invalid assurance schema document: {name}")


def _verify_graph_manifest(action_path: Path) -> None:
    manifest_path = action_path / "graph_manifest.json"
    if not manifest_path.is_file():
        raise AssuranceValidationError(
            f"Missing graph_manifest.json for action {action_path.name}"
        )
    manifest = _read_json(manifest_path)
    if not isinstance(manifest, dict):
        raise AssuranceValidationError(f"Invalid graph_manifest.json in {action_path.name}")
    entries = manifest.get("entries")
    if not isinstance(entries, list):
        raise AssuranceValidationError(
            f"graph_manifest.json missing entries for {action_path.name}"
        )
    for entry in entries:
        if not isinstance(entry, dict):
            raise AssuranceValidationError(
                f"Malformed graph_manifest entry in {action_path.name}"
            )
        rel = entry.get("path")
        digest = entry.get("digest")
        if not isinstance(rel, str) or not isinstance(digest, str):
            raise AssuranceValidationError(
                f"Malformed graph_manifest entry in {action_path.name}"
            )
        path = action_path / rel
        if not path.is_file():
            raise AssuranceValidationError(
                f"graph_manifest references missing file {rel} in {action_path.name}"
            )
        actual = file_sha256(path)
        if normalize_digest(actual) != normalize_digest(digest):
            raise AssuranceValidationError(
                f"Historical mutation detected: digest mismatch for {action_path.name}/{rel}"
            )


def validate_assurance_corpus(repo_root: Path) -> None:
    """Validate assurance schema registry and every corpus/assurance action chain."""
    repo_root = repo_root.resolve()
    validate_assurance_schema_registry(repo_root)

    index_path = repo_root / "corpus" / "assurance" / "index.json"
    if not index_path.is_file():
        # Empty scaffold is acceptable when no actions exist yet
        root = actions_root(repo_root)
        if root.is_dir() and any(p.is_dir() for p in root.iterdir()):
            raise AssuranceValidationError(
                "corpus/assurance/index.json missing but action stores exist"
            )
        return

    index = _read_json(index_path)
    if not isinstance(index, dict):
        raise AssuranceValidationError("corpus/assurance/index.json must be an object")
    validate_schema_version(index)
    action_ids = index.get("action_ids")
    if not isinstance(action_ids, list):
        raise AssuranceValidationError("corpus/assurance/index.json missing action_ids[]")

    root = actions_root(repo_root)
    on_disk = sorted(p.name for p in root.iterdir() if p.is_dir()) if root.is_dir() else []
    indexed = sorted(str(a) for a in action_ids)
    if on_disk != indexed:
        raise AssuranceValidationError(
            f"assurance index/action store mismatch: index={indexed} disk={on_disk}"
        )

    for action_id in indexed:
        action_path = root / action_id
        _verify_graph_manifest(action_path)
        result = validate_chain(repo_root, action_id, strict=False)
        if not result.get("ok"):
            raise AssuranceValidationError(f"Action chain validation failed for {action_id}")

        chain = load_chain(repo_root, action_id)
        for outcome in chain.outcomes.values():
            validate_outcome_record(repo_root, outcome)
        for calibration in chain.calibrations.values():
            validate_calibration_record(repo_root, calibration)

        manifest_path = action_path / "AssuranceReleaseManifest.v1.json"
        if manifest_path.is_file():
            man = _read_json(manifest_path)
            if isinstance(man, dict):
                validate_schema_version(man)
                validate_against_schema(
                    repo_root, "AssuranceReleaseManifest.v1.schema.json", man
                )
