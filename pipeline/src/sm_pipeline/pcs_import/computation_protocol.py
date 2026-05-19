"""Computation reproducibility protocol artifacts for PCS read models and lineage."""

from __future__ import annotations

from typing import Any

COMPUTATION_WORKFLOW_ID = "scientific_computation.reproducibility_v0"

COMPUTATION_LIMITATION_NOTICE = (
    "This artifact verifies declared computational provenance and hash consistency. "
    "It does not prove that the dataset is unbiased, that the model is scientifically valid, "
    "or that the result generalizes beyond the declared inputs and environment."
)

COMPUTATION_SUPPLEMENTAL_TYPES = frozenset(
    {
        "DatasetReceipt.v0",
        "EnvironmentReceipt.v0",
        "ComputationRunReceipt.v0",
        "ResultArtifact.v0",
        "ComputationWitness.v0",
    },
)

_COMPUTATION_READ_MODEL_KEYS = (
    "dataset_receipt",
    "environment_receipt",
    "computation_run_receipt",
    "result_artifact",
    "computation_witness",
)


def _payload(row: dict[str, Any]) -> dict[str, Any]:
    payload = row.get("payload")
    return payload if isinstance(payload, dict) else {}


def computation_lineage_from_supplemental(
    supplemental: list[dict[str, Any]],
) -> dict[str, Any]:
    """Extract indexable computation fields from supplemental protocol rows."""
    by_type: dict[str, dict[str, Any]] = {}
    for row in supplemental:
        artifact_type = str(row.get("artifact_type") or "")
        if artifact_type:
            by_type[artifact_type] = row

    out: dict[str, Any] = {}
    dataset = _payload(by_type.get("DatasetReceipt.v0", {}))
    if dataset:
        out["dataset_id"] = dataset.get("dataset_id")
        out["dataset_version"] = dataset.get("dataset_version")
        out["dataset_aggregate_hash"] = dataset.get("aggregate_hash")

    environment = _payload(by_type.get("EnvironmentReceipt.v0", {}))
    if environment:
        out["environment_id"] = environment.get("environment_id")

    run = _payload(by_type.get("ComputationRunReceipt.v0", {}))
    if run:
        out["run_id"] = run.get("run_id")
        out["code_commit"] = run.get("code_commit")
        out["command"] = run.get("command")

    result = _payload(by_type.get("ResultArtifact.v0", {}))
    if result:
        out["result_id"] = result.get("result_id")
        out["result_hash"] = result.get("sha256")

    witness = _payload(by_type.get("ComputationWitness.v0", {}))
    if witness:
        out["witness_id"] = witness.get("witness_id")
        out["witness_status"] = witness.get("status")
        out["dataset_hash"] = witness.get("dataset_hash")
        out["environment_hash"] = witness.get("environment_hash")
        out["run_receipt_hash"] = witness.get("run_receipt_hash")
        result_hashes = witness.get("result_hashes")
        if isinstance(result_hashes, list):
            out["result_hashes"] = [str(h) for h in result_hashes if h]

    return {k: v for k, v in out.items() if v not in (None, "", [])}


def attach_computation_artifacts(
    read_model: dict[str, Any],
    supplemental: list[dict[str, Any]],
) -> dict[str, Any]:
    """Promote computation protocol artifacts to first-class read-model fields."""
    from sm_pipeline.pcs_import.supplemental_protocol import protocol_artifact_to_named

    out = dict(read_model)
    by_type: dict[str, dict[str, Any]] = {}
    for row in supplemental:
        artifact_type = str(row.get("artifact_type") or "")
        if artifact_type in COMPUTATION_SUPPLEMENTAL_TYPES:
            by_type[artifact_type] = row

    mapping = {
        "DatasetReceipt.v0": "dataset_receipt",
        "EnvironmentReceipt.v0": "environment_receipt",
        "ComputationRunReceipt.v0": "computation_run_receipt",
        "ResultArtifact.v0": "result_artifact",
        "ComputationWitness.v0": "computation_witness",
    }
    for artifact_type, key in mapping.items():
        row = by_type.get(artifact_type)
        if row is not None:
            out[key] = protocol_artifact_to_named(row)

    remaining = [
        row
        for row in supplemental
        if str(row.get("artifact_type") or "") not in COMPUTATION_SUPPLEMENTAL_TYPES
        or str(row.get("artifact_type") or "") == "WorkflowProfile.v0"
    ]
    remaining = [r for r in remaining if str(r.get("artifact_type") or "") != "WorkflowProfile.v0"]
    if remaining:
        out["protocol_artifacts"] = remaining
    elif "protocol_artifacts" in out and not remaining:
        out.pop("protocol_artifacts", None)

    limitations = list(out.get("limitations") or [])
    if COMPUTATION_LIMITATION_NOTICE not in limitations:
        limitations.append(COMPUTATION_LIMITATION_NOTICE)
    out["limitations"] = limitations
    if not out.get("limitation_notice"):
        out["limitation_notice"] = COMPUTATION_LIMITATION_NOTICE

    return out


def is_computation_workflow(workflow_id: str | None) -> bool:
    return workflow_id == COMPUTATION_WORKFLOW_ID
