"""Export portable assurance action-chain bundles and portal data."""

from __future__ import annotations

import json
import os
import shutil
from pathlib import Path
from typing import Any

from sm_pipeline.assurance.graph import action_dir, load_chain, actions_root
from sm_pipeline.assurance.hashing import file_sha256
from sm_pipeline.assurance.models import utc_now_iso
from sm_pipeline.assurance.validate import (
    AssuranceValidationError,
    calibration_to_portal_read_model,
    outcome_to_portal_read_model,
)


def _write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _copy_tree_files(src: Path, dest: Path, rel_prefix: str) -> list[tuple[str, str]]:
    entries: list[tuple[str, str]] = []
    if not src.is_dir():
        return entries
    for path in sorted(src.rglob("*")):
        if not path.is_file():
            continue
        rel = f"{rel_prefix}/{path.relative_to(src).as_posix()}"
        out = dest / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, out)
        entries.append((rel, file_sha256(out)))
    return entries


def export_action_chain(
    repo_root: Path,
    action_id: str,
    out_dir: Path,
    *,
    release_id: str | None = None,
) -> Path:
    chain = load_chain(repo_root, action_id)
    src = action_dir(repo_root, action_id)
    out = out_dir.resolve()
    if out.exists() and any(out.iterdir()):
        raise AssuranceValidationError(f"Export directory not empty: {out}")
    out.mkdir(parents=True, exist_ok=True)

    checksum_entries: list[tuple[str, str]] = []
    for sub, prefix in (
        ("refs", "refs"),
        ("execution", "execution"),
        ("outcomes", "outcomes"),
        ("calibrations", "calibrations"),
        ("nodes", "nodes"),
        ("edges", "edges"),
    ):
        checksum_entries.extend(_copy_tree_files(src / sub, out, prefix))

    # Nested PCS pointers from nodes
    claim_pointers: list[dict[str, str]] = []
    for node in chain.nodes.values():
        pcs_id = node.get("pcs_claim_id")
        if not pcs_id:
            continue
        claim_dir = repo_root / "corpus" / "pcs" / "claims" / pcs_id
        digest = None
        for cand in ("read_model.json", "claim_artifact.json"):
            p = claim_dir / cand
            if p.is_file():
                digest = file_sha256(p)
                break
        if digest:
            claim_pointers.append({"claim_id": pcs_id, "digest": digest})

    def paths_for(prefix: str) -> list[dict[str, str]]:
        return [{"path": rel, "digest": dig} for rel, dig in checksum_entries if rel.startswith(prefix + "/")]

    rid = release_id or f"assurance-export-{action_id}"
    manifest = {
        "schema_version": "v1",
        "release_id": rid,
        "action_id": action_id,
        "created_at": utc_now_iso(),
        "lifecycle": "admissible_for_import",
        "producer": "sm_pipeline.assurance.export",
        "artifacts": {
            "refs": paths_for("refs"),
            "pcs": {
                "mode": "claim_pointers" if claim_pointers else "none",
                "bundle_path": None,
                "claim_pointers": claim_pointers,
            },
            "execution": paths_for("execution"),
            "outcomes": paths_for("outcomes"),
            "calibrations": paths_for("calibrations"),
            "nodes": paths_for("nodes"),
            "edges": paths_for("edges"),
        },
        "checksums_path": "checksums.txt",
        "notes": "Portable action-chain export",
    }
    _write_json(out / "AssuranceReleaseManifest.v1.json", manifest)
    checksum_entries.append(
        ("AssuranceReleaseManifest.v1.json", file_sha256(out / "AssuranceReleaseManifest.v1.json"))
    )

    lines = [f"{dig}  {rel}" for rel, dig in checksum_entries if rel != "checksums.txt"]
    # Re-hash manifest already included; write checksums without self-ref
    (out / "checksums.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return out


def _redact_node(node: dict[str, Any], *, include_internal: bool) -> dict[str, Any] | None:
    privacy = node.get("privacy") or "public"
    if privacy == "public":
        return node
    if include_internal and privacy == "internal":
        return node
    # Strip payload for non-public in public export
    redacted = dict(node)
    redacted["payload"] = None
    if privacy == "redacted" or (privacy == "internal" and not include_internal):
        redacted["summary"] = "[redacted]"
        return redacted
    return redacted


def build_assurance_portal_export(
    repo_root: Path,
    *,
    include_internal: bool | None = None,
) -> dict[str, Any]:
    if include_internal is None:
        include_internal = os.environ.get("ASSURANCE_INCLUDE_INTERNAL") == "1"
    actions: dict[str, Any] = {}
    root = actions_root(repo_root)
    action_ids: list[str] = []
    if root.is_dir():
        for action_path in sorted(root.iterdir()):
            if not action_path.is_dir():
                continue
            action_id = action_path.name
            chain = load_chain(repo_root, action_id)
            nodes = []
            for node in chain.nodes.values():
                redacted = _redact_node(node, include_internal=include_internal)
                if redacted is not None:
                    nodes.append(redacted)
            outcomes = [
                outcome_to_portal_read_model(o)
                for o in chain.outcomes.values()
                if include_internal or (o.get("privacy") or "public") == "public"
            ]
            calibrations = [
                calibration_to_portal_read_model(c)
                for c in chain.calibrations.values()
                if include_internal or (c.get("privacy") or "public") == "public"
            ]
            chronology = sorted(
                nodes,
                key=lambda n: (n.get("created_at") or "", n.get("node_id") or ""),
            )
            from sm_pipeline.assurance.graph import list_gaps

            actions[action_id] = {
                "action_id": action_id,
                "nodes": nodes,
                "edges": list(chain.edges.values()),
                "outcomes": outcomes,
                "calibrations": calibrations,
                "gaps": list_gaps(chain),
                "chronology": [
                    {
                        "node_id": n["node_id"],
                        "node_class": n["node_class"],
                        "created_at": n.get("created_at"),
                        "summary": n.get("summary"),
                        "evidence_classes": n.get("evidence_classes") or [],
                    }
                    for n in chronology
                ],
            }
            action_ids.append(action_id)
    return {
        "schema_version": "AssurancePortalExport.v1",
        "generated_at": utc_now_iso(),
        "include_internal": bool(include_internal),
        "action_ids": action_ids,
        "actions": actions,
    }


def write_assurance_portal_export(repo_root: Path) -> Path:
    export = build_assurance_portal_export(repo_root)
    out_dir = repo_root.resolve() / "portal" / ".generated"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "assurance-export.json"
    out_path.write_text(json.dumps(export, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return out_path
