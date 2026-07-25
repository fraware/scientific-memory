"""Append-only action-chain graph store and queries."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import networkx as nx

from sm_pipeline.assurance.hashing import content_digest, file_sha256, normalize_digest
from sm_pipeline.assurance.models import ActionChainEdge, ActionChainNode, utc_now_iso
from sm_pipeline.assurance.validate import AssuranceValidationError, validate_against_schema, validate_schema_version


REQUIRED_NODE_CLASSES = (
    "source",
    "evidence",
    "claim",
    "proposed_action",
    "admissibility_decision",
    "review",
    "grant",
    "runtime_action",
    "verification_result",
)


@dataclass
class ActionChain:
    action_id: str
    nodes: dict[str, dict[str, Any]] = field(default_factory=dict)
    edges: dict[str, dict[str, Any]] = field(default_factory=dict)
    outcomes: dict[str, dict[str, Any]] = field(default_factory=dict)
    calibrations: dict[str, dict[str, Any]] = field(default_factory=dict)

    def to_networkx(self) -> nx.DiGraph:
        g = nx.DiGraph()
        for node_id, node in self.nodes.items():
            g.add_node(node_id, **node)
        for edge in self.edges.values():
            g.add_edge(edge["from_node_id"], edge["to_node_id"], **edge)
        return g


def actions_root(repo_root: Path) -> Path:
    return repo_root.resolve() / "corpus" / "assurance" / "actions"


def action_dir(repo_root: Path, action_id: str) -> Path:
    return actions_root(repo_root) / action_id


def _read_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise AssuranceValidationError(f"Expected object in {path}")
    return data


def _write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def load_chain(repo_root: Path, action_id: str) -> ActionChain:
    root = action_dir(repo_root, action_id)
    if not root.is_dir():
        raise AssuranceValidationError(f"Unknown action_id: {action_id}")
    chain = ActionChain(action_id=action_id)
    nodes_dir = root / "nodes"
    if nodes_dir.is_dir():
        for path in sorted(nodes_dir.glob("*.json")):
            node = _read_json(path)
            chain.nodes[str(node["node_id"])] = node
    edges_dir = root / "edges"
    if edges_dir.is_dir():
        for path in sorted(edges_dir.glob("*.json")):
            edge = _read_json(path)
            chain.edges[str(edge["edge_id"])] = edge
    outcomes_dir = root / "outcomes"
    if outcomes_dir.is_dir():
        for path in sorted(outcomes_dir.glob("*.json")):
            outcome = _read_json(path)
            chain.outcomes[str(outcome["outcome_id"])] = outcome
    calibrations_dir = root / "calibrations"
    if calibrations_dir.is_dir():
        for path in sorted(calibrations_dir.glob("*.json")):
            cal = _read_json(path)
            chain.calibrations[str(cal["calibration_id"])] = cal
    return chain


def write_graph_manifest(repo_root: Path, action_id: str) -> dict[str, Any]:
    root = action_dir(repo_root, action_id)
    entries: list[dict[str, str]] = []
    for sub in ("nodes", "edges", "outcomes", "calibrations"):
        d = root / sub
        if not d.is_dir():
            continue
        for path in sorted(d.glob("*.json")):
            rel = f"{sub}/{path.name}"
            entries.append({"path": rel, "digest": file_sha256(path)})
    manifest = {
        "schema_version": "v1",
        "action_id": action_id,
        "updated_at": utc_now_iso(),
        "entries": entries,
    }
    _write_json(root / "graph_manifest.json", manifest)
    return manifest


def _ensure_immutable_write(path: Path, data: dict[str, Any], digest: str) -> bool:
    """Write if absent; idempotent if same digest; error if conflict. Returns True if written."""
    if path.exists():
        existing = _read_json(path)
        existing_digest = existing.get("content_digest") or (existing.get("integrity") or {}).get(
            "content_digest"
        )
        if existing_digest and normalize_digest(str(existing_digest)) == normalize_digest(digest):
            return False
        # Compare file digest of existing content
        if normalize_digest(file_sha256(path)) == normalize_digest(digest):
            return False
        raise AssuranceValidationError(
            f"Historical mutation rejected for {path.name}: digest conflict"
        )
    _write_json(path, data)
    return True


def append_node(repo_root: Path, node: dict[str, Any], *, validate: bool = True) -> ActionChainNode:
    validate_schema_version(node)
    if validate:
        validate_against_schema(repo_root, "ActionChainNode.v1.schema.json", node)
    action_id = str(node["action_id"])
    node_id = str(node["node_id"])
    digest = str(node.get("content_digest") or "")
    if not digest:
        digest = content_digest(node, digest_fields=("content_digest",))
        node = {**node, "content_digest": digest}
    path = action_dir(repo_root, action_id) / "nodes" / f"{node_id}.json"
    _ensure_immutable_write(path, node, digest)
    write_graph_manifest(repo_root, action_id)
    return ActionChainNode.model_validate(node)


def append_edge(repo_root: Path, edge: dict[str, Any], *, validate: bool = True) -> ActionChainEdge:
    validate_schema_version(edge)
    if validate:
        validate_against_schema(repo_root, "ActionChainEdge.v1.schema.json", edge)
    action_id = str(edge["action_id"])
    edge_id = str(edge["edge_id"])
    digest = str(edge.get("content_digest") or "")
    if not digest:
        digest = content_digest(edge, digest_fields=("content_digest",))
        edge = {**edge, "content_digest": digest}
    path = action_dir(repo_root, action_id) / "edges" / f"{edge_id}.json"
    # Cycle check before write (idempotent same-digest skips still OK)
    if not path.exists():
        chain = load_chain(repo_root, action_id)
        g = chain.to_networkx()
        g.add_edge(edge["from_node_id"], edge["to_node_id"])
        if not nx.is_directed_acyclic_graph(g):
            raise AssuranceValidationError("Cycle introduction rejected")
    _ensure_immutable_write(path, edge, digest)
    write_graph_manifest(repo_root, action_id)
    return ActionChainEdge.model_validate(edge)


def list_gaps(chain: ActionChain, *, strict: bool = False) -> list[dict[str, str]]:
    gaps: list[dict[str, str]] = []
    present_classes = {n.get("node_class") for n in chain.nodes.values()}
    for cls in REQUIRED_NODE_CLASSES:
        if cls not in present_classes:
            gaps.append({"gap_id": f"missing_node_class:{cls}", "reason": f"Missing node class {cls}"})
    for outcome_id, outcome in chain.outcomes.items():
        if outcome.get("delayed_result_status") == "delayed_unresolved":
            gaps.append(
                {
                    "gap_id": f"delayed_outcome:{outcome_id}",
                    "reason": "Unresolved delayed outcome",
                }
            )
    if "outcome" not in present_classes and not chain.outcomes:
        gaps.append({"gap_id": "missing_outcome", "reason": "No outcome node or record"})
    if "calibration_update" not in present_classes and not chain.calibrations:
        gaps.append({"gap_id": "missing_calibration", "reason": "No calibration node or record"})
    if strict and gaps:
        raise AssuranceValidationError(
            "Strict validate-action-chain failed: " + "; ".join(g["reason"] for g in gaps)
        )
    return gaps


def _verify_stored_digests(repo_root: Path, action_id: str) -> None:
    """Fail closed if on-disk files diverge from graph_manifest digests."""
    root = action_dir(repo_root, action_id)
    manifest_path = root / "graph_manifest.json"
    if not manifest_path.is_file():
        return
    manifest = _read_json(manifest_path)
    for entry in manifest.get("entries") or []:
        rel = entry.get("path")
        digest = entry.get("digest")
        if not isinstance(rel, str) or not isinstance(digest, str):
            raise AssuranceValidationError("Malformed graph_manifest entry")
        path = root / rel
        if not path.is_file():
            raise AssuranceValidationError(f"graph_manifest references missing file: {rel}")
        actual = file_sha256(path)
        if normalize_digest(actual) != normalize_digest(digest):
            raise AssuranceValidationError(
                f"Historical mutation rejected for {rel}: digest conflict"
            )


def validate_chain(
    repo_root: Path,
    action_id: str,
    *,
    strict: bool = False,
) -> dict[str, Any]:
    chain = load_chain(repo_root, action_id)
    _verify_stored_digests(repo_root, action_id)
    g = chain.to_networkx()
    if not nx.is_directed_acyclic_graph(g):
        raise AssuranceValidationError("Action chain contains a cycle")
    for node in chain.nodes.values():
        validate_schema_version(node)
        validate_against_schema(repo_root, "ActionChainNode.v1.schema.json", node)
        declared = node.get("content_digest")
        if declared:
            computed = content_digest(node, digest_fields=("content_digest",))
            if normalize_digest(str(declared)) != normalize_digest(computed):
                raise AssuranceValidationError(
                    f"Node content_digest mismatch for {node.get('node_id')}"
                )
    for edge in chain.edges.values():
        validate_schema_version(edge)
        validate_against_schema(repo_root, "ActionChainEdge.v1.schema.json", edge)
        if edge["from_node_id"] not in chain.nodes or edge["to_node_id"] not in chain.nodes:
            raise AssuranceValidationError(
                f"Edge {edge['edge_id']} references missing node"
            )
        declared = edge.get("content_digest")
        if declared:
            computed = content_digest(edge, digest_fields=("content_digest",))
            if normalize_digest(str(declared)) != normalize_digest(computed):
                raise AssuranceValidationError(
                    f"Edge content_digest mismatch for {edge.get('edge_id')}"
                )
    gaps = list_gaps(chain, strict=strict)
    return {
        "action_id": action_id,
        "ok": True,
        "node_count": len(chain.nodes),
        "edge_count": len(chain.edges),
        "outcome_count": len(chain.outcomes),
        "calibration_count": len(chain.calibrations),
        "gaps": gaps,
        "acyclic": True,
    }


def query_path(chain: ActionChain, from_node: str, to_node: str) -> list[str]:
    g = chain.to_networkx()
    if from_node not in g or to_node not in g:
        raise AssuranceValidationError("Path endpoints must exist in the chain")
    try:
        return list(nx.shortest_path(g, from_node, to_node))
    except nx.NetworkXNoPath as exc:
        raise AssuranceValidationError(f"No path from {from_node} to {to_node}") from exc


def update_assurance_index(repo_root: Path) -> None:
    root = actions_root(repo_root)
    root.mkdir(parents=True, exist_ok=True)
    action_ids = sorted(p.name for p in root.iterdir() if p.is_dir())
    index = {"schema_version": "v1", "action_ids": action_ids}
    index_path = repo_root.resolve() / "corpus" / "assurance" / "index.json"
    _write_json(index_path, index)
