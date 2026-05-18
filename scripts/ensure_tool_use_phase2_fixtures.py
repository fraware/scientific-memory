#!/usr/bin/env python3
"""Pin commits and align Phase 2 tool-use release fixtures for strict SM import."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DIR = REPO_ROOT / "tests" / "pcs" / "fixtures" / "tool-use-release"
PCS_CORE_TOOL_USE = REPO_ROOT.parent / "pcs-core" / "examples" / "tool-use-release"
PCS_CORE_REGISTRY = REPO_ROOT.parent / "pcs-core" / "examples" / "artifact_registry.valid.json"
VENDORED_REGISTRY_V0 = REPO_ROOT / "schemas" / "pcs" / "ArtifactRegistry.v0.json"
TOOL_USE_WORKFLOW_PROFILE_ID = "agent_tool_use.safety_v0"

# Placeholder commits in pcs-core conformance examples -> pinned RC hashes.
COMMIT_REPLACEMENTS = {
    "d444444444444444444444444444444444444444": "a361fd2b388f88cdbc9e4e4691ae49dba714ab6c",
    "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa": "4c5439ae358733f9a4c4a58e33fdaed1ab0d29de",
    "b222222222222222222222222222222222222222": "cb6848001e2e60a484e04eba5ad6be3fe2e4eccc",
    "c333333333333333333333333333333333333333": "0f659b90c80c46a6bbfd51b0d37ea723b032fb9d",
    "a111111111111111111111111111111111111111": "4c5439ae358733f9a4c4a58e33fdaed1ab0d29de",
    "e444444444444444444444444444444444444444": "c4259a4cb79fe7b195fd156feb346c08fc334d33",
}


def _replace_commits_in_file(path: Path) -> bool:
    text = path.read_text(encoding="utf-8")
    updated = text
    for old, new in COMMIT_REPLACEMENTS.items():
        updated = updated.replace(old, new)
    if updated != text:
        path.write_text(updated, encoding="utf-8")
        return True
    return False


def _align_signed_bundle_to_tool_use_artifacts(release_dir: Path) -> None:
    """Align embedded SCB receipts/certificates with sibling tool-use protocol files."""
    bundle_path = release_dir / "signed_science_claim_bundle.json"
    receipt_path = release_dir / "runtime_receipt.json"
    cert_path = release_dir / "tool_use_certificate.json"
    if not bundle_path.is_file() or not receipt_path.is_file() or not cert_path.is_file():
        return

    bundle = json.loads(bundle_path.read_text(encoding="utf-8-sig"))
    receipt = json.loads(receipt_path.read_text(encoding="utf-8-sig"))
    cert = json.loads(cert_path.read_text(encoding="utf-8-sig"))
    scb = bundle.get("science_claim_bundle")
    if not isinstance(scb, dict):
        return

    trace_hash = str(cert.get("trace_hash") or receipt.get("trace_hash") or "")
    receipts = scb.get("runtime_receipts")
    if isinstance(receipts, list) and receipts and isinstance(receipts[0], dict):
        merged = dict(receipts[0])
        for key, value in receipt.items():
            if key in merged:
                merged[key] = value
        if trace_hash:
            merged["trace_hash"] = trace_hash
        receipts[0] = merged

    certs = scb.get("certificates")
    if isinstance(certs, list):
        for entry in certs:
            if not isinstance(entry, dict):
                continue
            if entry.get("certificate_id") == cert.get("certificate_id"):
                entry["trace_hash"] = cert.get("trace_hash", trace_hash)
                if cert.get("status"):
                    entry["status"] = cert.get("status")
                if cert.get("source_commit"):
                    entry["source_commit"] = cert.get("source_commit")

    bundle_path.write_text(json.dumps(bundle, indent=2) + "\n", encoding="utf-8")


def _pin_scientific_memory_commit(release_dir: Path) -> None:
    sys.path.insert(0, str(REPO_ROOT / "pipeline" / "src"))
    from sm_pipeline.pcs_import.provenance import git_head_commit

    head = git_head_commit(REPO_ROOT)
    if not head:
        return
    for name in ("release_manifest.v0.json", "ReleaseManifest.v0.json"):
        path = release_dir / name
        if not path.is_file():
            continue
        manifest = json.loads(path.read_text(encoding="utf-8-sig"))
        producer_repos = dict(manifest.get("producer_repos") or {})
        sm = dict(producer_repos.get("scientific_memory") or {})
        sm["commit"] = head
        producer_repos["scientific_memory"] = sm
        manifest["producer_repos"] = producer_repos
        artifacts = dict(manifest.get("artifacts") or {})
        for artifact_name, entry in artifacts.items():
            if not isinstance(entry, dict):
                continue
            if entry.get("source_repo", "").endswith("scientific-memory"):
                entry["source_commit"] = head
        manifest["artifacts"] = artifacts
        path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def _sync_manifest_hashes(release_dir: Path) -> None:
    sys.path.insert(0, str(REPO_ROOT / "pipeline" / "src"))
    from sm_pipeline.pcs_validate.canonical_hash import canonical_hash, file_sha256_digest
    from sm_pipeline.pcs_validate.release_paths import (
        resolve_release_chain_validation_path,
        resolve_release_manifest_path,
    )

    validation_path = resolve_release_chain_validation_path(release_dir)
    if validation_path.is_file():
        validation = json.loads(validation_path.read_text(encoding="utf-8-sig"))
        validation["signature_or_digest"] = canonical_hash(validation)
        validation_path.write_text(json.dumps(validation, indent=2) + "\n", encoding="utf-8")

    manifest_path = resolve_release_manifest_path(release_dir)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    artifacts = manifest.get("artifacts")
    if isinstance(artifacts, dict):
        for name, entry in artifacts.items():
            if not isinstance(entry, dict):
                continue
            artifact_path = release_dir / name
            if artifact_path.is_file():
                entry["sha256"] = file_sha256_digest(artifact_path)
    chain_ref = manifest.get("release_chain_validation_result")
    if isinstance(chain_ref, dict) and validation_path.is_file():
        chain_ref["sha256"] = file_sha256_digest(validation_path)
        if not chain_ref.get("path"):
            chain_ref["path"] = validation_path.name
    manifest["signature_or_digest"] = canonical_hash(
        {key: value for key, value in manifest.items() if key != "signature_or_digest"},
    )
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def _align_release_chain_validation(validation_path: Path) -> bool:
    try:
        from pcs_core.registry_semantics import responsible_component_for_registry_refs
    except (ImportError, SyntaxError, ModuleNotFoundError):
        def responsible_component_for_registry_refs(refs: frozenset[str]) -> str:  # noqa: ARG001
            return "CertifyEdge"

    data = json.loads(validation_path.read_text(encoding="utf-8-sig"))
    if not isinstance(data, dict):
        return False
    checks = data.get("checks")
    if not isinstance(checks, list):
        return False

    changed = False
    for check in checks:
        if not isinstance(check, dict):
            continue
        refs = check.get("registry_check_refs")
        if refs is None:
            check["registry_check_refs"] = []
            refs = []
            changed = True
        if not isinstance(refs, list):
            continue
        if not check.get("responsible_component"):
            frozen = frozenset(ref for ref in refs if isinstance(ref, str))
            check["responsible_component"] = responsible_component_for_registry_refs(frozen)
            changed = True

    if data.get("workflow_profile_id") != TOOL_USE_WORKFLOW_PROFILE_ID:
        data["workflow_profile_id"] = TOOL_USE_WORKFLOW_PROFILE_ID
        changed = True

    if changed:
        sys.path.insert(0, str(REPO_ROOT / "pipeline" / "src"))
        from sm_pipeline.pcs_validate.canonical_hash import canonical_hash

        data["signature_or_digest"] = canonical_hash(data)
        validation_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return changed


def _copy_workflow_profile(release_dir: Path) -> None:
    profile_sources = [
        REPO_ROOT / "schemas" / "pcs" / "workflow_profiles" / "tool_use_safety.valid.json",
        REPO_ROOT.parent / "pcs-core" / "examples" / "workflow_profiles" / "tool_use_safety.valid.json",
    ]
    for src in profile_sources:
        if src.is_file():
            shutil.copy2(src, release_dir / "workflow_profile.v0.json")
            return


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--release-dir", type=Path, default=DEFAULT_DIR)
    args = parser.parse_args()
    release_dir = args.release_dir.resolve()
    if not release_dir.is_dir():
        print(f"error: missing release dir {release_dir}", file=sys.stderr)
        return 1

    sys.path.insert(0, str(REPO_ROOT / "pipeline" / "src"))
    from sm_pipeline.pcs_validate.release_paths import (
        resolve_release_chain_validation_path,
        resolve_release_manifest_path,
    )
    from sm_pipeline.pcs_validate.release_chain_validation import validate_release_chain_validation
    from sm_pipeline.pcs_validate.release_manifest import validate_release_manifest

    for path in sorted(release_dir.glob("*.json")):
        if _replace_commits_in_file(path):
            print(f"pinned commits -> {path.name}")

    _pin_scientific_memory_commit(release_dir)
    _align_signed_bundle_to_tool_use_artifacts(release_dir)
    _copy_workflow_profile(release_dir)

    if PCS_CORE_REGISTRY.is_file():
        shutil.copy2(PCS_CORE_REGISTRY, release_dir / "ArtifactRegistry.v0.json")
        VENDORED_REGISTRY_V0.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(PCS_CORE_REGISTRY, VENDORED_REGISTRY_V0)

    validation_path = resolve_release_chain_validation_path(release_dir)
    if validation_path.is_file():
        if _align_release_chain_validation(validation_path):
            print(f"aligned validation -> {validation_path}")

    _sync_manifest_hashes(release_dir)

    manifest_path = resolve_release_manifest_path(release_dir)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    manifest_errors = validate_release_manifest(manifest_path, repo_root=REPO_ROOT)
    if manifest_errors:
        for err in manifest_errors:
            print(f"error: manifest: {err}", file=sys.stderr)
        return 1

    validation_errors = validate_release_chain_validation(
        validation_path,
        repo_root=REPO_ROOT,
        expected_release_id=str(manifest.get("release_id") or ""),
    )
    if validation_errors:
        for err in validation_errors:
            print(f"error: validation: {err}", file=sys.stderr)
        return 1

    _write_phase2_read_model_fixture(release_dir)
    print(f"OK: tool-use Phase 2 fixtures valid in {release_dir}")
    return 0


def _write_phase2_read_model_fixture(release_dir: Path) -> None:
    """Commit a portal-contract golden read model beside the release fixtures."""
    import shutil
    import tempfile

    sys.path.insert(0, str(REPO_ROOT / "pipeline" / "src"))
    from sm_pipeline.pcs_import.release_manifest_importer import import_release_manifest
    from sm_pipeline.pcs_validate.release_paths import resolve_release_manifest_path

    schemas_src = REPO_ROOT / "schemas"
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        if schemas_src.is_dir():
            shutil.copytree(schemas_src, root / "schemas")
        dest = root / "release"
        shutil.copytree(release_dir, dest)
        manifest = resolve_release_manifest_path(dest)
        result = import_release_manifest(manifest, repo_root=root, write=True, render=False)
        read_model = root / "corpus" / "pcs" / "claims" / result.claim_id / "read_model.json"
        out = release_dir / ".phase2-read-model.json"
        shutil.copy2(read_model, out)
        print(f"wrote portal contract fixture -> {out}")


if __name__ == "__main__":
    raise SystemExit(main())
