"""Append outcome / calibration records onto an existing action chain."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from sm_pipeline.assurance.graph import (
    action_dir,
    append_edge,
    append_node,
    load_chain,
    update_assurance_index,
    write_graph_manifest,
)
from sm_pipeline.assurance.hashing import content_digest
from sm_pipeline.assurance.models import utc_now_iso
from sm_pipeline.assurance.validate import (
    AssuranceValidationError,
    reject_duplicate_outcome_id,
    validate_calibration_record,
    validate_outcome_record,
)


def _write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def add_outcome(repo_root: Path, outcome_path: Path) -> dict[str, Any]:
    data = json.loads(outcome_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise AssuranceValidationError("Outcome must be a JSON object")
    record = validate_outcome_record(repo_root, data)
    action_id = record.action_id
    chain = load_chain(repo_root, action_id)
    reject_duplicate_outcome_id(set(chain.outcomes.keys()), record.outcome_id)

    dest = action_dir(repo_root, action_id) / "outcomes" / f"{record.outcome_id}.json"
    if dest.exists():
        raise AssuranceValidationError(f"Duplicate outcome_id rejected: {record.outcome_id}")
    _write_json(dest, data)

    node_id = f"node-outcome-{record.outcome_id}"
    node: dict[str, Any] = {
        "schema_version": "v1",
        "node_id": node_id,
        "action_id": action_id,
        "node_class": "outcome",
        "summary": f"Outcome {record.outcome_id}",
        "created_at": utc_now_iso(),
        "privacy": record.privacy,
        "evidence_classes": list(record.evidence_classes),
        "payload_ref": f"outcomes/{record.outcome_id}.json",
    }
    node["content_digest"] = content_digest(node, digest_fields=("content_digest",))
    append_node(repo_root, node)

    # Link from verification_result if present, else from runtime_action
    from_id = None
    for n in chain.nodes.values():
        if n.get("node_class") == "verification_result":
            from_id = n["node_id"]
            break
    if from_id is None:
        for n in chain.nodes.values():
            if n.get("node_class") == "runtime_action":
                from_id = n["node_id"]
                break
    if from_id is not None:
        edge: dict[str, Any] = {
            "schema_version": "v1",
            "edge_id": f"edge-realizes-{record.outcome_id}",
            "action_id": action_id,
            "from_node_id": from_id,
            "to_node_id": node_id,
            "relation": "realizes",
            "created_at": utc_now_iso(),
        }
        edge["content_digest"] = content_digest(edge, digest_fields=("content_digest",))
        append_edge(repo_root, edge)

    write_graph_manifest(repo_root, action_id)
    update_assurance_index(repo_root)
    return {"action_id": action_id, "outcome_id": record.outcome_id, "node_id": node_id}


def add_calibration(repo_root: Path, calibration_path: Path) -> dict[str, Any]:
    data = json.loads(calibration_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise AssuranceValidationError("Calibration must be a JSON object")
    record = validate_calibration_record(repo_root, data)
    action_id = record.action_id
    chain = load_chain(repo_root, action_id)
    if record.calibration_id in chain.calibrations:
        raise AssuranceValidationError(
            f"Duplicate calibration_id rejected: {record.calibration_id}"
        )

    dest = action_dir(repo_root, action_id) / "calibrations" / f"{record.calibration_id}.json"
    _write_json(dest, data)

    node_id = f"node-calibration-{record.calibration_id}"
    node: dict[str, Any] = {
        "schema_version": "v1",
        "node_id": node_id,
        "action_id": action_id,
        "node_class": "calibration_update",
        "summary": f"Calibration {record.calibration_id}",
        "created_at": utc_now_iso(),
        "privacy": record.privacy,
        "evidence_classes": ["human_reviewed"],
        "payload_ref": f"calibrations/{record.calibration_id}.json",
    }
    node["content_digest"] = content_digest(node, digest_fields=("content_digest",))
    append_node(repo_root, node)

    chain2 = load_chain(repo_root, action_id)
    from_id = None
    for n in chain2.nodes.values():
        if n.get("node_class") == "outcome":
            from_id = n["node_id"]
    if from_id is None:
        for n in chain2.nodes.values():
            if n.get("node_class") == "replication":
                from_id = n["node_id"]
                break
    if from_id is not None:
        edge = {
            "schema_version": "v1",
            "edge_id": f"edge-calibrates-{record.calibration_id}",
            "action_id": action_id,
            "from_node_id": from_id,
            "to_node_id": node_id,
            "relation": "calibrates",
            "created_at": utc_now_iso(),
        }
        edge["content_digest"] = content_digest(edge, digest_fields=("content_digest",))
        append_edge(repo_root, edge)

    write_graph_manifest(repo_root, action_id)
    update_assurance_index(repo_root)
    return {
        "action_id": action_id,
        "calibration_id": record.calibration_id,
        "node_id": node_id,
    }


def add_replication_node(
    repo_root: Path,
    action_id: str,
    *,
    replication_id: str,
    summary: str,
    privacy: str = "public",
) -> dict[str, Any]:
    """Append a replication node (never mutates prior outcome nodes)."""
    chain = load_chain(repo_root, action_id)
    node_id = f"node-replication-{replication_id}"
    if node_id in chain.nodes:
        raise AssuranceValidationError(f"Duplicate replication node: {node_id}")
    node: dict[str, Any] = {
        "schema_version": "v1",
        "node_id": node_id,
        "action_id": action_id,
        "node_class": "replication",
        "summary": summary,
        "created_at": utc_now_iso(),
        "privacy": privacy,
        "evidence_classes": ["empirically_measured"],
    }
    node["content_digest"] = content_digest(node, digest_fields=("content_digest",))
    append_node(repo_root, node)
    from_id = None
    for n in chain.nodes.values():
        if n.get("node_class") == "outcome":
            from_id = n["node_id"]
    if from_id:
        edge = {
            "schema_version": "v1",
            "edge_id": f"edge-replicates-{replication_id}",
            "action_id": action_id,
            "from_node_id": from_id,
            "to_node_id": node_id,
            "relation": "replicates",
            "created_at": utc_now_iso(),
        }
        edge["content_digest"] = content_digest(edge, digest_fields=("content_digest",))
        append_edge(repo_root, edge)
    write_graph_manifest(repo_root, action_id)
    return {"action_id": action_id, "node_id": node_id}
