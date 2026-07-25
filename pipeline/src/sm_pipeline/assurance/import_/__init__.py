"""Assurance release importer."""

from __future__ import annotations

import json
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from sm_pipeline.assurance.graph import (
    append_edge,
    append_node,
    update_assurance_index,
    write_graph_manifest,
    action_dir,
)
from sm_pipeline.assurance.hashing import file_sha256, normalize_digest
from sm_pipeline.assurance.models import AssuranceReleaseManifest, utc_now_iso
from sm_pipeline.assurance.validate import (
    AssuranceValidationError,
    validate_against_schema,
    validate_calibration_record,
    validate_outcome_record,
    validate_schema_version,
)


@dataclass
class ImportReport:
    release_id: str
    action_id: str
    ok: bool
    written_paths: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "v1",
            "release_id": self.release_id,
            "action_id": self.action_id,
            "ok": self.ok,
            "written_paths": self.written_paths,
            "errors": self.errors,
            "warnings": self.warnings,
            "created_at": utc_now_iso(),
        }


def _parse_checksums(path: Path) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if len(parts) < 2:
            raise AssuranceValidationError(f"Malformed checksums line: {line!r}")
        digest, rel = parts[0], parts[-1]
        mapping[rel.replace("\\", "/")] = normalize_digest(digest)
    return mapping


def _verify_path_digest(release_dir: Path, rel: str, expected: str) -> None:
    path = release_dir / rel
    if not path.is_file():
        raise AssuranceValidationError(f"Missing release artifact: {rel}")
    actual = file_sha256(path)
    if normalize_digest(actual) != normalize_digest(expected):
        raise AssuranceValidationError(
            f"Digest mismatch for {rel}: expected={expected} actual={actual}"
        )


def _resolve_pcs_pointers(repo_root: Path, pointers: list[dict[str, str]]) -> None:
    claims_root = repo_root / "corpus" / "pcs" / "claims"
    for pointer in pointers:
        claim_id = pointer["claim_id"]
        expected = pointer["digest"]
        claim_dir = claims_root / claim_id
        if not claim_dir.is_dir():
            raise AssuranceValidationError(
                f"Missing PCS claim pointer target: {claim_id}"
            )
        # Prefer read_model digest if present; else signature_or_digest from claim artifact
        candidates = [
            claim_dir / "read_model.json",
            claim_dir / "claim_artifact.json",
            claim_dir / "signed_science_claim_bundle.json",
        ]
        found = False
        for cand in candidates:
            if cand.is_file():
                data = json.loads(cand.read_text(encoding="utf-8"))
                digest = None
                if isinstance(data, dict):
                    digest = data.get("signature_or_digest") or data.get("content_digest")
                    if not digest and "claim" in data and isinstance(data["claim"], dict):
                        digest = data["claim"].get("signature_or_digest")
                if digest and normalize_digest(str(digest)) == normalize_digest(expected):
                    found = True
                    break
                # Also accept file hash match
                if normalize_digest(file_sha256(cand)) == normalize_digest(expected):
                    found = True
                    break
        if not found:
            raise AssuranceValidationError(
                f"PCS claim digest mismatch or unresolved for {claim_id}"
            )


def import_assurance_release(
    release_path: Path,
    *,
    repo_root: Path | None = None,
    write: bool = True,
) -> ImportReport:
    root = (repo_root or Path(__file__).resolve().parents[4]).resolve()
    release_dir = release_path.resolve()
    if release_dir.is_file():
        release_dir = release_dir.parent
    manifest_path = release_dir / "AssuranceReleaseManifest.v1.json"
    if not manifest_path.is_file():
        raise AssuranceValidationError(
            f"Missing AssuranceReleaseManifest.v1.json in {release_dir}"
        )

    raw = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise AssuranceValidationError("Manifest must be an object")
    validate_schema_version(raw)
    validate_against_schema(root, "AssuranceReleaseManifest.v1.schema.json", raw)
    manifest = AssuranceReleaseManifest.model_validate(raw)

    report = ImportReport(release_id=manifest.release_id, action_id=manifest.action_id, ok=False)

    if manifest.lifecycle not in ("admissible_for_import", "imported"):
        raise AssuranceValidationError(
            f"Lifecycle not admissible for import: {manifest.lifecycle}"
        )

    checksums_path = release_dir / manifest.checksums_path
    if not checksums_path.is_file():
        raise AssuranceValidationError("Missing checksums.txt")
    checksums = _parse_checksums(checksums_path)

    # Verify every declared artifact path
    declared: list[tuple[str, str]] = []
    arts = manifest.artifacts
    for group in (arts.refs, arts.execution, arts.outcomes, arts.calibrations, arts.nodes, arts.edges):
        for item in group:
            declared.append((item.path, item.digest))
    if arts.pcs.mode == "bundle" and arts.pcs.bundle_path:
        # Bundle path must appear in checksums
        bp = arts.pcs.bundle_path
        if bp not in checksums:
            raise AssuranceValidationError(f"PCS bundle path missing from checksums: {bp}")
        declared.append((bp, checksums[bp]))

    for rel, digest in declared:
        if rel not in checksums:
            raise AssuranceValidationError(f"Path missing from checksums.txt: {rel}")
        if normalize_digest(checksums[rel]) != normalize_digest(digest):
            raise AssuranceValidationError(
                f"Checksum conflict for {rel}: manifest={digest} checksums={checksums[rel]}"
            )
        _verify_path_digest(release_dir, rel, digest)

    # Identity / ambiguity checks
    outcome_ids: set[str] = set()
    for item in arts.outcomes:
        data = json.loads((release_dir / item.path).read_text(encoding="utf-8"))
        oid = str(data.get("outcome_id") or "")
        if not oid:
            raise AssuranceValidationError(f"Outcome missing outcome_id: {item.path}")
        if oid in outcome_ids:
            raise AssuranceValidationError(f"Ambiguous dual outcome IDs: {oid}")
        outcome_ids.add(oid)
        if str(data.get("action_id")) != manifest.action_id:
            raise AssuranceValidationError(
                f"Outcome action_id conflict: {data.get('action_id')} != {manifest.action_id}"
            )
        validate_outcome_record(root, data)

    cal_ids: set[str] = set()
    for item in arts.calibrations:
        data = json.loads((release_dir / item.path).read_text(encoding="utf-8"))
        cid = str(data.get("calibration_id") or "")
        if not cid:
            raise AssuranceValidationError(f"Calibration missing calibration_id: {item.path}")
        if cid in cal_ids:
            raise AssuranceValidationError(f"Ambiguous dual calibration IDs: {cid}")
        cal_ids.add(cid)
        if str(data.get("action_id")) != manifest.action_id:
            raise AssuranceValidationError("Calibration action_id conflict")
        validate_calibration_record(root, data)

    node_ids: set[str] = set()
    node_classes: set[str] = set()
    for item in arts.nodes:
        data = json.loads((release_dir / item.path).read_text(encoding="utf-8"))
        nid = str(data.get("node_id") or "")
        if not nid:
            raise AssuranceValidationError(f"Node missing node_id: {item.path}")
        if nid in node_ids:
            raise AssuranceValidationError(f"Ambiguous dual node IDs: {nid}")
        node_ids.add(nid)
        if str(data.get("action_id")) != manifest.action_id:
            raise AssuranceValidationError(
                f"Node action_id conflict: {data.get('action_id')} != {manifest.action_id}"
            )
        node_classes.add(str(data.get("node_class") or ""))
        validate_schema_version(data)
        validate_against_schema(root, "ActionChainNode.v1.schema.json", data)

    edge_ids: set[str] = set()
    for item in arts.edges:
        data = json.loads((release_dir / item.path).read_text(encoding="utf-8"))
        eid = str(data.get("edge_id") or "")
        if not eid:
            raise AssuranceValidationError(f"Edge missing edge_id: {item.path}")
        if eid in edge_ids:
            raise AssuranceValidationError(f"Ambiguous dual edge IDs: {eid}")
        edge_ids.add(eid)
        if str(data.get("action_id")) != manifest.action_id:
            raise AssuranceValidationError(
                f"Edge action_id conflict: {data.get('action_id')} != {manifest.action_id}"
            )
        validate_schema_version(data)
        validate_against_schema(root, "ActionChainEdge.v1.schema.json", data)
        if data.get("from_node_id") not in node_ids or data.get("to_node_id") not in node_ids:
            raise AssuranceValidationError(
                f"Edge {eid} references node missing from release"
            )

    # Fail closed on partial releases missing required decision/runtime classes
    from sm_pipeline.assurance.graph import REQUIRED_NODE_CLASSES

    missing_required = [c for c in REQUIRED_NODE_CLASSES if c not in node_classes]
    if missing_required:
        raise AssuranceValidationError(
            "Partial release rejected; missing required node classes: "
            + ", ".join(missing_required)
        )

    # PCS resolution
    if arts.pcs.mode == "claim_pointers":
        if not arts.pcs.claim_pointers:
            raise AssuranceValidationError("PCS claim_pointers mode requires pointers")
        _resolve_pcs_pointers(
            root,
            [p.model_dump() for p in arts.pcs.claim_pointers],
        )
    elif arts.pcs.mode == "bundle":
        if not arts.pcs.bundle_path:
            raise AssuranceValidationError("PCS bundle mode requires bundle_path")
        bundle_file = release_dir / arts.pcs.bundle_path
        if not bundle_file.is_file():
            raise AssuranceValidationError(f"Missing PCS bundle: {arts.pcs.bundle_path}")
        # Optional nested import when write=True
        if write:
            try:
                from sm_pipeline.pcs_import.science_claim_bundle_importer import (
                    import_signed_bundle,
                )

                import_signed_bundle(
                    bundle_file,
                    repo_root=root,
                    strict=False,
                    release_mode=False,
                    allow_legacy=True,
                    write=True,
                    pin_fixture_report=False,
                )
            except Exception as exc:  # noqa: BLE001
                # Fail closed if caller included a bundle that cannot import
                raise AssuranceValidationError(
                    f"Nested PCS bundle import failed: {exc}"
                ) from exc
    elif arts.pcs.mode == "none":
        report.warnings.append("PCS mode=none; no PCS evidence attached")

    if not write:
        report.ok = True
        return report

    dest = action_dir(root, manifest.action_id)
    dest.mkdir(parents=True, exist_ok=True)

    for item in arts.refs:
        dest_path = dest / "refs" / Path(item.path).name
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(release_dir / item.path, dest_path)
        report.written_paths.append(str(dest_path.relative_to(root)))

    for item in arts.execution:
        dest_path = dest / "execution" / Path(item.path).name
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(release_dir / item.path, dest_path)
        report.written_paths.append(str(dest_path.relative_to(root)))

    for item in arts.outcomes:
        dest_path = dest / "outcomes" / Path(item.path).name
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(release_dir / item.path, dest_path)
        report.written_paths.append(str(dest_path.relative_to(root)))

    for item in arts.calibrations:
        dest_path = dest / "calibrations" / Path(item.path).name
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(release_dir / item.path, dest_path)
        report.written_paths.append(str(dest_path.relative_to(root)))

    for item in arts.nodes:
        node = json.loads((release_dir / item.path).read_text(encoding="utf-8"))
        append_node(root, node, validate=True)
        report.written_paths.append(f"corpus/assurance/actions/{manifest.action_id}/nodes/{node['node_id']}.json")

    for item in arts.edges:
        edge = json.loads((release_dir / item.path).read_text(encoding="utf-8"))
        append_edge(root, edge, validate=True)
        report.written_paths.append(f"corpus/assurance/actions/{manifest.action_id}/edges/{edge['edge_id']}.json")

    shutil.copy2(manifest_path, dest / "AssuranceReleaseManifest.v1.json")
    shutil.copy2(checksums_path, dest / "checksums.txt")
    write_graph_manifest(root, manifest.action_id)
    update_assurance_index(root)

    report_path = dest / "import_report.json"
    report.ok = True
    report_path.write_text(
        json.dumps(report.to_dict(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    report.written_paths.append(str(report_path.relative_to(root)))
    return report
