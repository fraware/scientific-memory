"""Shared builders for assurance test fixtures."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from sm_pipeline.assurance.hashing import content_digest, file_sha256
from sm_pipeline.assurance.validate import seal_integrity

NODE_CLASSES = [
    "source",
    "evidence",
    "claim",
    "proposed_action",
    "admissibility_decision",
    "review",
    "grant",
    "runtime_action",
    "verification_result",
]


def make_node(
    action_id: str,
    node_class: str,
    *,
    privacy: str = "public",
    evidence_classes: list[str] | None = None,
    pcs_claim_id: str | None = None,
    summary: str | None = None,
) -> dict[str, Any]:
    node: dict[str, Any] = {
        "schema_version": "v1",
        "node_id": f"node-{node_class}",
        "action_id": action_id,
        "node_class": node_class,
        "summary": summary or f"{node_class} for {action_id}",
        "created_at": "2026-07-01T00:00:00Z",
        "privacy": privacy,
        "evidence_classes": evidence_classes
        or (["human_reviewed"] if node_class in ("review", "grant") else ["unchecked_advisory"]),
        "payload_ref": None,
        "pcs_claim_id": pcs_claim_id,
        "external_ref_ids": [],
        "payload": None,
    }
    node["content_digest"] = content_digest(node, digest_fields=("content_digest",))
    return node


def make_edge(
    action_id: str,
    from_class: str,
    to_class: str,
    relation: str,
) -> dict[str, Any]:
    edge: dict[str, Any] = {
        "schema_version": "v1",
        "edge_id": f"edge-{from_class}-to-{to_class}",
        "action_id": action_id,
        "from_node_id": f"node-{from_class}",
        "to_node_id": f"node-{to_class}",
        "relation": relation,
        "created_at": "2026-07-01T00:00:00Z",
        "notes": None,
    }
    edge["content_digest"] = content_digest(edge, digest_fields=("content_digest",))
    return edge


def base_outcome(action_id: str, outcome_id: str, **overrides: Any) -> dict[str, Any]:
    data: dict[str, Any] = {
        "schema_version": "v1",
        "outcome_id": outcome_id,
        "action_id": action_id,
        "scientific_question_id": "q-1",
        "claim_ids": ["claim-demo-1"],
        "proposed_action_id": "pa-1",
        "external_refs": [],
        "pcs_claim_ids": [],
        "intervention_performed": {"summary": "Ran protocol A", "performed_at": "2026-07-02T00:00:00Z"},
        "protocol": {"protocol_id": "proto-1", "description": "Synthetic protocol", "version": "1"},
        "protocol_deviations": [],
        "measured_result": {
            "summary": "Yield within band",
            "result_kind": "quantitative",
            "value": 0.82,
            "units": "fraction",
        },
        "data_commitments": {
            "source_digests": [
                {
                    "name": "raw.csv",
                    "digest": "sha256:" + ("a" * 64),
                }
            ],
            "notes": None,
        },
        "uncertainty": {"statement": "±5% relative", "quantitative": None},
        "adverse_events": [],
        "missing_data": {"has_missing_data": False, "fields": []},
        "delayed_result_status": "not_delayed",
        "reviewer_assessment": {"status": "accepted", "notes": None, "reviewer_identity": "reviewer-1"},
        "replication_status": "not_attempted",
        "environment_context": {"summary": "Lab bench", "instrument_ids": ["inst-1"], "site": "lab-a"},
        "privacy": "public",
        "evidence_classes": ["empirically_measured", "human_reviewed"],
    }
    data.update(overrides)
    return seal_integrity(data, writer_identity="fixture-builder", created_at="2026-07-02T12:00:00Z")


def base_calibration(action_id: str, calibration_id: str, **overrides: Any) -> dict[str, Any]:
    data: dict[str, Any] = {
        "schema_version": "v1",
        "calibration_id": calibration_id,
        "action_id": action_id,
        "decision_basis": {"summary": "Prior success estimate from similar runs", "decision_node_id": "node-admissibility_decision"},
        "prediction_presence": {
            "success": True,
            "information_gain": False,
            "cost": True,
            "time": True,
            "risk": False,
        },
        "predicted_success": 0.7,
        "predicted_information_gain": None,
        "predicted_cost": 100.0,
        "predicted_time": 3600.0,
        "predicted_risk": None,
        "realized_outcome_id": "outcome-1",
        "calibration_class": "well_calibrated",
        "admissibility_error": False,
        "prioritization_error": False,
        "authorization_error": False,
        "verifier_disagreement": {"present": False, "summary": None},
        "uncertainty": {"statement": "Prediction from historical rates"},
        "missingness": {"has_missing_fields": False, "fields": []},
        "aggregation_eligibility": True,
        "realized_success": True,
        "realized_information_gain": None,
        "realized_cost": 110.0,
        "realized_time": 4000.0,
        "privacy": "public",
    }
    data.update(overrides)
    return seal_integrity(data, writer_identity="fixture-builder", created_at="2026-07-03T12:00:00Z")


CHAIN_RELATIONS = [
    ("source", "evidence", "supports"),
    ("evidence", "claim", "supports"),
    ("claim", "proposed_action", "proposes"),
    ("proposed_action", "admissibility_decision", "decides"),
    ("admissibility_decision", "review", "reviews"),
    ("review", "grant", "grants"),
    ("grant", "runtime_action", "executes"),
    ("runtime_action", "verification_result", "verifies"),
]


def write_release_bundle(
    dest: Path,
    action_id: str,
    *,
    release_id: str = "assurance-release-demo",
    with_outcome: bool = True,
    with_calibration: bool = True,
    delayed: bool = False,
    pcs_mode: str = "none",
) -> Path:
    dest.mkdir(parents=True, exist_ok=True)
    for sub in ("refs", "pcs", "execution", "outcomes", "calibrations", "nodes", "edges"):
        (dest / sub).mkdir(parents=True, exist_ok=True)

    nodes = [make_node(action_id, c) for c in NODE_CLASSES]
    edges = [make_edge(action_id, a, b, rel) for a, b, rel in CHAIN_RELATIONS]

    if with_outcome:
        outcome = base_outcome(
            action_id,
            "outcome-1",
            delayed_result_status="delayed_unresolved" if delayed else "not_delayed",
            measured_result={
                "summary": "Pending" if delayed else "Yield within band",
                "result_kind": "not_yet_available" if delayed else "quantitative",
                "value": None if delayed else 0.82,
                "units": None if delayed else "fraction",
            },
        )
        (dest / "outcomes" / "outcome-1.json").write_text(
            json.dumps(outcome, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        onode = make_node(action_id, "outcome", evidence_classes=["empirically_measured"], summary="Outcome outcome-1")
        onode["node_id"] = "node-outcome-outcome-1"
        onode["payload_ref"] = "outcomes/outcome-1.json"
        onode["content_digest"] = content_digest(onode, digest_fields=("content_digest",))
        nodes.append(onode)
        edge_out = {
            "schema_version": "v1",
            "edge_id": "edge-verification_result-to-outcome",
            "action_id": action_id,
            "from_node_id": "node-verification_result",
            "to_node_id": "node-outcome-outcome-1",
            "relation": "realizes",
            "created_at": "2026-07-01T00:00:00Z",
            "notes": None,
        }
        edge_out["content_digest"] = content_digest(edge_out, digest_fields=("content_digest",))
        edges.append(edge_out)

    if with_calibration:
        cal = base_calibration(action_id, "cal-1")
        if delayed:
            cal = base_calibration(
                action_id,
                "cal-1",
                aggregation_eligibility=False,
                realized_outcome_id=None,
                calibration_class="not_aggregable",
                missingness={
                    "has_missing_fields": True,
                    "fields": [{"field": "realized_outcome_id", "reason": "delayed unresolved"}],
                },
            )
        (dest / "calibrations" / "cal-1.json").write_text(
            json.dumps(cal, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        cnode = make_node(
            action_id,
            "calibration_update",
            evidence_classes=["human_reviewed"],
            summary="Calibration cal-1",
        )
        cnode["node_id"] = "node-calibration-cal-1"
        cnode["payload_ref"] = "calibrations/cal-1.json"
        cnode["content_digest"] = content_digest(cnode, digest_fields=("content_digest",))
        nodes.append(cnode)
        edge = {
            "schema_version": "v1",
            "edge_id": "edge-outcome-to-calibration",
            "action_id": action_id,
            "from_node_id": "node-outcome-outcome-1" if with_outcome else "node-verification_result",
            "to_node_id": "node-calibration-cal-1",
            "relation": "calibrates",
            "created_at": "2026-07-01T00:00:00Z",
            "notes": None,
        }
        edge["content_digest"] = content_digest(edge, digest_fields=("content_digest",))
        edges.append(edge)

    for node in nodes:
        (dest / "nodes" / f"{node['node_id']}.json").write_text(
            json.dumps(node, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
    for edge in edges:
        (dest / "edges" / f"{edge['edge_id']}.json").write_text(
            json.dumps(edge, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )

    exec_doc = {"schema_version": "v1", "execution_id": "exec-1", "summary": "Synthetic execution"}
    (dest / "execution" / "execution.json").write_text(
        json.dumps(exec_doc, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    def entries(subdir: str) -> list[dict[str, str]]:
        out = []
        for path in sorted((dest / subdir).glob("*.json")):
            rel = f"{subdir}/{path.name}"
            out.append({"path": rel, "digest": file_sha256(path)})
        return out

    manifest = {
        "schema_version": "v1",
        "release_id": release_id,
        "action_id": action_id,
        "created_at": "2026-07-01T00:00:00Z",
        "lifecycle": "admissible_for_import",
        "producer": "assurance-fixture",
        "artifacts": {
            "refs": [],
            "pcs": {"mode": pcs_mode, "bundle_path": None, "claim_pointers": []},
            "execution": entries("execution"),
            "outcomes": entries("outcomes"),
            "calibrations": entries("calibrations"),
            "nodes": entries("nodes"),
            "edges": entries("edges"),
        },
        "checksums_path": "checksums.txt",
        "notes": "Synthetic assurance release",
    }
    man_path = dest / "AssuranceReleaseManifest.v1.json"
    man_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    lines = []
    for group in (
        manifest["artifacts"]["execution"],
        manifest["artifacts"]["outcomes"],
        manifest["artifacts"]["calibrations"],
        manifest["artifacts"]["nodes"],
        manifest["artifacts"]["edges"],
    ):
        for item in group:
            lines.append(f"{item['digest']}  {item['path']}")
    lines.append(f"{file_sha256(man_path)}  AssuranceReleaseManifest.v1.json")
    (dest / "checksums.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return dest
