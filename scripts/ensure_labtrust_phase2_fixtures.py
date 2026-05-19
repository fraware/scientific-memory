#!/usr/bin/env python3
"""Ensure Phase 2 protocol fixtures exist beside labtrust-release chain artifacts."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DIR = REPO_ROOT / "tests" / "pcs" / "fixtures" / "labtrust-release"
PCS_CORE_EXAMPLES = REPO_ROOT.parent / "pcs-core" / "examples"
PCS_CORE_LABTRUST = PCS_CORE_EXAMPLES / "labtrust-release"
PCS_CORE_REGISTRY = PCS_CORE_EXAMPLES / "artifact_registry.valid.json"
VENDORED_REGISTRY_VALID = REPO_ROOT / "schemas" / "pcs" / "artifact_registry.valid.json"
VENDORED_REGISTRY_V0 = REPO_ROOT / "schemas" / "pcs" / "ArtifactRegistry.v0.json"
HANDOFF_GLOB = "handoff_manifest.*.v0.json"

PHASE2_FILES = (
    "ReleaseManifest.v0.json",
    "ReleaseChainValidationResult.v0.json",
)

LABTRUST_WORKFLOW_PROFILE_ID = "labtrust.qc_release_v0.1"
LABTRUST_SOURCE_REPO = "https://github.com/fraware/LabTrust-Gym"

IMPORT_REPORT_TEMPLATE = {
    "allow_legacy": False,
    "bundle_shape": "pcs_core",
    "claim_id": "claim-pcs-qc-release-v0.1",
    "imported_at": "2026-05-17T15:39:09Z",
    "render_path": "/pcs/claims/claim-pcs-qc-release-v0.1",
    "source_bundle_path": "tests/pcs/fixtures/labtrust-release/signed_science_claim_bundle.json",
    "stale_artifacts": [],
    "strict": True,
    "verification_status": "passed",
    "warnings": [],
    "source_repo": "https://github.com/fraware/scientific-memory",
    "release_id": "release-pcs-v0.1-labtrust-qc",
    "release_candidate": "pcs-v0.1.0-rc1",
    "release_manifest_path": "tests/pcs/fixtures/labtrust-release/ReleaseManifest.v0.json",
    "validation_profile": "labtrust-v0.1-release-chain",
    "release_chain_validation_id": "validation-pcs-v0.1-labtrust-qc-rc",
    "release_chain_validation_status": "ProofChecked",
    "release_chain_validator": "pcs-core",
    "release_chain_checked_at": "2026-05-17T17:01:22Z",
}


def _pin_rc_fixture_commits(release_dir: Path) -> None:
    """Keep labtrust-release fixtures aligned with pcs-core published SM commit."""
    if release_dir.resolve() != DEFAULT_DIR.resolve():
        return
    sys.path.insert(0, str(REPO_ROOT / "pipeline" / "src"))
    from sm_pipeline.pcs_import.pcs_core_release_align import align_legacy_fixture_scientific_memory_commit

    align_legacy_fixture_scientific_memory_commit(release_dir, repo_root=REPO_ROOT)


def _pin_scientific_memory_commit_in_legacy(release_dir: Path) -> None:
    import json

    sys.path.insert(0, str(REPO_ROOT / "pipeline" / "src"))
    from sm_pipeline.pcs_import.provenance import git_head_commit

    legacy_path = release_dir / "RELEASE_FIXTURE_MANIFEST.json"
    if not legacy_path.is_file():
        return
    legacy = json.loads(legacy_path.read_text(encoding="utf-8-sig"))
    head = git_head_commit(REPO_ROOT)
    if head:
        legacy["scientific_memory_commit"] = head
        legacy_path.write_text(json.dumps(legacy, indent=2) + "\n", encoding="utf-8")


def _signed_certificate_id(release_dir: Path) -> str | None:
    signed_path = release_dir / "signed_science_claim_bundle.json"
    if not signed_path.is_file():
        return None
    signed = json.loads(signed_path.read_text(encoding="utf-8-sig"))
    scb = signed.get("science_claim_bundle")
    if not isinstance(scb, dict):
        return None
    certs = scb.get("certificates")
    if not isinstance(certs, list) or not certs or not isinstance(certs[0], dict):
        return None
    cert_id = certs[0].get("certificate_id")
    return cert_id if isinstance(cert_id, str) and cert_id else None


def _labtrust_gym_commit_from_runtime_receipt(release_dir: Path) -> str | None:
    receipt_path = release_dir / "runtime_receipt.json"
    if not receipt_path.is_file():
        return None
    receipt = json.loads(receipt_path.read_text(encoding="utf-8-sig"))
    commit = receipt.get("source_commit")
    return commit if isinstance(commit, str) and commit else None


def _patch_labtrust_gym_provenance(obj: Any, commit: str) -> bool:
    changed = False
    if isinstance(obj, dict):
        if obj.get("source_repo") == LABTRUST_SOURCE_REPO and obj.get("source_commit") != commit:
            obj["source_commit"] = commit
            changed = True
        for value in obj.values():
            if _patch_labtrust_gym_provenance(value, commit):
                changed = True
    elif isinstance(obj, list):
        for item in obj:
            if _patch_labtrust_gym_provenance(item, commit):
                changed = True
    return changed


def _rehash_science_claim_bundle(bundle: dict[str, Any]) -> None:
    sys.path.insert(0, str(REPO_ROOT / "pipeline" / "src"))
    from sm_pipeline.pcs_validate.canonical_hash import canonical_hash

    assumption_set = bundle.get("assumption_set")
    if isinstance(assumption_set, dict):
        assumption_set["signature_or_digest"] = canonical_hash(assumption_set)

    claim = bundle.get("claim_artifact")
    if isinstance(claim, dict):
        claim["signature_or_digest"] = canonical_hash(claim)

    receipts = bundle.get("runtime_receipts")
    receipt_digests: dict[str, str] = {}
    if isinstance(receipts, list):
        for receipt in receipts:
            if isinstance(receipt, dict):
                receipt["signature_or_digest"] = canonical_hash(receipt)
                receipt_id = receipt.get("receipt_id")
                digest = receipt.get("signature_or_digest")
                if isinstance(receipt_id, str) and isinstance(digest, str):
                    receipt_digests[receipt_id] = digest

    cert_digests: dict[str, str] = {}
    certs = bundle.get("certificates")
    if isinstance(certs, list):
        for cert in certs:
            if isinstance(cert, dict):
                cert["signature_or_digest"] = canonical_hash(cert)
                cert_id = cert.get("certificate_id")
                digest = cert.get("signature_or_digest")
                if isinstance(cert_id, str) and isinstance(digest, str):
                    cert_digests[cert_id] = digest

    claim_id = claim.get("artifact_id") if isinstance(claim, dict) else None
    claim_digest = claim.get("signature_or_digest") if isinstance(claim, dict) else None

    evidence = bundle.get("evidence_bundle")
    if isinstance(evidence, dict):
        artifact_hashes = evidence.get("artifact_hashes")
        if isinstance(artifact_hashes, dict):
            if isinstance(claim_id, str) and isinstance(claim_digest, str):
                artifact_hashes[claim_id] = claim_digest
            for cert_id, digest in cert_digests.items():
                artifact_hashes[cert_id] = digest
            for receipt_id, digest in receipt_digests.items():
                artifact_hashes[receipt_id] = digest
        evidence["signature_or_digest"] = canonical_hash(evidence)

    bundle["signature_or_digest"] = canonical_hash(bundle)


def _sync_certified_bundle_hash_references(release_dir: Path) -> bool:
    """After certified bundle bytes change, align PF verification + signed bundle hash pins."""
    certified_path = release_dir / "science_claim_bundle.certified.json"
    if not certified_path.is_file():
        return False

    sys.path.insert(0, str(REPO_ROOT / "pipeline" / "src"))
    from sm_pipeline.pcs_validate.canonical_hash import canonical_hash, file_sha256_digest

    certified_hash = file_sha256_digest(certified_path)
    changed = False

    vr_path = release_dir / "verification_result.json"
    if vr_path.is_file():
        vr = json.loads(vr_path.read_text(encoding="utf-8-sig"))
        verified = vr.get("verified_input")
        if isinstance(verified, dict) and verified.get("bundle_hash") != certified_hash:
            verified["bundle_hash"] = certified_hash
            vr["verified_input"] = verified
            vr["signature_or_digest"] = canonical_hash(vr)
            vr_path.write_text(json.dumps(vr, indent=2) + "\n", encoding="utf-8")
            changed = True

    signed_path = release_dir / "signed_science_claim_bundle.json"
    if signed_path.is_file():
        signed = json.loads(signed_path.read_text(encoding="utf-8-sig"))
        signed_changed = False
        if signed.get("signed_input_bundle_hash") != certified_hash:
            signed["signed_input_bundle_hash"] = certified_hash
            signed_changed = True
        embedded_vr = signed.get("verification_result")
        if isinstance(embedded_vr, dict):
            embedded_verified = embedded_vr.get("verified_input")
            if isinstance(embedded_verified, dict) and embedded_verified.get("bundle_hash") != certified_hash:
                embedded_verified["bundle_hash"] = certified_hash
                embedded_vr["verified_input"] = embedded_verified
                embedded_vr["signature_or_digest"] = canonical_hash(embedded_vr)
                signed["verification_result"] = embedded_vr
                signed_changed = True
        if signed_changed:
            signed["signature_or_digest"] = canonical_hash(signed)
            signed_path.write_text(json.dumps(signed, indent=2) + "\n", encoding="utf-8")
            changed = True

    return changed


def _align_labtrust_gym_source_commits(release_dir: Path) -> bool:
    """Pin all LabTrust-Gym provenance to runtime_receipt.source_commit (manifest authority)."""
    commit = _labtrust_gym_commit_from_runtime_receipt(release_dir)
    if not commit:
        return False

    changed = False
    bundle_paths = (
        release_dir / "science_claim_bundle.pending.json",
        release_dir / "science_claim_bundle.certified.json",
    )
    for path in bundle_paths:
        if not path.is_file():
            continue
        bundle = json.loads(path.read_text(encoding="utf-8-sig"))
        if _patch_labtrust_gym_provenance(bundle, commit):
            _rehash_science_claim_bundle(bundle)
            path.write_text(json.dumps(bundle, indent=2) + "\n", encoding="utf-8")
            changed = True

    signed_path = release_dir / "signed_science_claim_bundle.json"
    if signed_path.is_file():
        signed = json.loads(signed_path.read_text(encoding="utf-8-sig"))
        scb = signed.get("science_claim_bundle")
        if isinstance(scb, dict) and _patch_labtrust_gym_provenance(scb, commit):
            _rehash_science_claim_bundle(scb)
            sys.path.insert(0, str(REPO_ROOT / "pipeline" / "src"))
            from sm_pipeline.pcs_validate.canonical_hash import canonical_hash

            signed["signature_or_digest"] = canonical_hash(signed)
            signed_path.write_text(json.dumps(signed, indent=2) + "\n", encoding="utf-8")
            changed = True

    return changed


def _align_labtrust_bundle_certificate_identity(release_dir: Path) -> bool:
    """Keep certified bundle and trace certificate certificate_id aligned with the signed bundle."""
    sys.path.insert(0, str(REPO_ROOT / "pipeline" / "src"))
    from sm_pipeline.pcs_validate.canonical_hash import canonical_hash

    cert_id = _signed_certificate_id(release_dir)
    if not cert_id:
        return False

    changed = False
    certified_path = release_dir / "science_claim_bundle.certified.json"
    if certified_path.is_file():
        certified = json.loads(certified_path.read_text(encoding="utf-8-sig"))
        if _first_certificate_id(certified) != cert_id:
            certs = certified.get("certificates")
            if isinstance(certs, list) and certs and isinstance(certs[0], dict):
                old_id = certs[0].get("certificate_id")
                certs[0]["certificate_id"] = cert_id
                claim = certified.get("claim_artifact")
                if isinstance(claim, dict) and isinstance(claim.get("certificate_refs"), list):
                    claim["certificate_refs"] = [
                        cert_id if ref == old_id else ref for ref in claim["certificate_refs"]
                    ]
                evidence = certified.get("evidence_bundle")
                if isinstance(evidence, dict):
                    refs = evidence.get("certificate_refs")
                    if isinstance(refs, list):
                        evidence["certificate_refs"] = [
                            cert_id if ref == old_id else ref for ref in refs
                        ]
                    ah = evidence.get("artifact_hashes")
                    if isinstance(ah, dict) and isinstance(old_id, str) and old_id in ah:
                        ah[cert_id] = ah.pop(old_id)
                _rehash_science_claim_bundle(certified)
                certified_path.write_text(json.dumps(certified, indent=2) + "\n", encoding="utf-8")
                changed = True

    trace_cert_path = release_dir / "trace_certificate.json"
    if trace_cert_path.is_file():
        trace_cert = json.loads(trace_cert_path.read_text(encoding="utf-8-sig"))
        if trace_cert.get("certificate_id") != cert_id:
            trace_cert["certificate_id"] = cert_id
            trace_cert["signature_or_digest"] = canonical_hash(trace_cert)
            trace_cert_path.write_text(json.dumps(trace_cert, indent=2) + "\n", encoding="utf-8")
            changed = True

    return changed


def _first_certificate_id(bundle: dict) -> str | None:
    certs = bundle.get("certificates")
    if not isinstance(certs, list) or not certs or not isinstance(certs[0], dict):
        return None
    cert_id = certs[0].get("certificate_id")
    return cert_id if isinstance(cert_id, str) else None


def _sync_legacy_manifest_producer_commits(release_dir: Path) -> None:
    """Pin RELEASE_FIXTURE_MANIFEST producer commits to on-disk artifact source_commit fields."""
    legacy_path = release_dir / "RELEASE_FIXTURE_MANIFEST.json"
    if not legacy_path.is_file():
        return
    legacy = json.loads(legacy_path.read_text(encoding="utf-8-sig"))
    trace_cert_path = release_dir / "trace_certificate.json"
    signed_path = release_dir / "signed_science_claim_bundle.json"
    lt_commit = _labtrust_gym_commit_from_runtime_receipt(release_dir)
    if lt_commit:
        legacy["labtrust_gym_commit"] = lt_commit
    if trace_cert_path.is_file():
        trace_cert = json.loads(trace_cert_path.read_text(encoding="utf-8-sig"))
        commit = trace_cert.get("source_commit")
        if isinstance(commit, str) and commit:
            legacy["certifyedge_commit"] = commit
    if signed_path.is_file():
        signed = json.loads(signed_path.read_text(encoding="utf-8-sig"))
        for key in ("verification_result",):
            artifact = signed.get(key)
            if isinstance(artifact, dict):
                commit = artifact.get("source_commit")
                if isinstance(commit, str) and commit:
                    legacy["provability_fabric_commit"] = commit
                    break
        else:
            commit = signed.get("source_commit")
            if isinstance(commit, str) and commit:
                legacy["provability_fabric_commit"] = commit
    legacy_path.write_text(json.dumps(legacy, indent=2) + "\n", encoding="utf-8")


def _sync_legacy_manifest_artifact_hashes(release_dir: Path) -> None:
    from sm_pipeline.pcs_validate.canonical_hash import file_sha256_digest

    legacy_path = release_dir / "RELEASE_FIXTURE_MANIFEST.json"
    legacy = json.loads(legacy_path.read_text(encoding="utf-8-sig"))
    artifacts = legacy.get("artifacts")
    if isinstance(artifacts, dict):
        for name in list(artifacts):
            path = release_dir / name
            if path.is_file():
                artifacts[name] = file_sha256_digest(path)
    legacy_path.write_text(json.dumps(legacy, indent=2) + "\n", encoding="utf-8")


def _build_profile_scoped_deferred_checks(
    chain_checks: list[dict],
    workflow_profile_id: str | None,
) -> list[dict]:
    from pcs_core.registry_semantics import (
        PCS_CORE_COMPONENT,
        collect_chain_registry_refs,
        deferral_reason,
        enforcement_layer,
        lookup_registry_check,
    )
    from pcs_core.workflow_profiles import required_release_blocking_refs_for_profile

    cited = collect_chain_registry_refs(chain_checks)
    required = required_release_blocking_refs_for_profile(workflow_profile_id)
    deferred: list[dict] = []
    for ref in sorted(required - cited):
        found = lookup_registry_check(ref)
        if found is None:
            continue
        _artifact_type, check = found
        check_id = str(check.get("check_id"))
        layer = enforcement_layer(check)
        if layer == "release_chain":
            continue
        deferred.append(
            {
                "registry_ref": ref,
                "status": "deferred",
                "enforcement_location": layer,
                "responsible_component": str(
                    check.get("responsible_component") or PCS_CORE_COMPONENT,
                ),
                "reason": deferral_reason(check_id),
            },
        )
    return deferred


def _mirror_fixture_tree_to_release_run() -> None:
    """Keep release-run aligned with the labtrust fixture after ensure regenerates Phase 2 metadata."""
    release_run = (REPO_ROOT / "release-run").resolve()
    if not release_run.is_dir():
        return
    for path in sorted(DEFAULT_DIR.iterdir()):
        if path.is_file() and not path.name.startswith("."):
            shutil.copy2(path, release_run / path.name)
    print(f"mirrored labtrust fixture -> {release_run}")


def _align_release_chain_validation(validation_path: Path) -> bool:
    """Add pcs-core required fields (responsible_component, deferred_registry_checks)."""
    try:
        from pcs_core.registry_semantics import responsible_component_for_registry_refs
    except ImportError:
        return False

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

    if not data.get("workflow_profile_id"):
        data["workflow_profile_id"] = LABTRUST_WORKFLOW_PROFILE_ID
        changed = True

    profile_id = str(data.get("workflow_profile_id") or LABTRUST_WORKFLOW_PROFILE_ID)
    deferred = _build_profile_scoped_deferred_checks(checks, profile_id)
    if data.get("deferred_registry_checks") != deferred:
        data["deferred_registry_checks"] = deferred
        changed = True

    if changed:
        sys.path.insert(0, str(REPO_ROOT / "pipeline" / "src"))
        from sm_pipeline.pcs_validate.canonical_hash import canonical_hash

        data["signature_or_digest"] = canonical_hash(data)
        validation_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return changed


def _resolve_scientific_memory_commit(release_dir: Path) -> str | None:
    sys.path.insert(0, str(REPO_ROOT / "pipeline" / "src"))
    from sm_pipeline.pcs_import.pcs_core_release_align import pcs_core_scientific_memory_commit
    from sm_pipeline.pcs_import.provenance import git_head_commit

    if release_dir.resolve() == (REPO_ROOT / "release-run").resolve():
        return git_head_commit(REPO_ROOT) or pcs_core_scientific_memory_commit(REPO_ROOT)
    commit = pcs_core_scientific_memory_commit(REPO_ROOT)
    if commit:
        return commit
    legacy_path = release_dir / "RELEASE_FIXTURE_MANIFEST.json"
    if legacy_path.is_file():
        legacy = json.loads(legacy_path.read_text(encoding="utf-8-sig"))
        legacy_commit = legacy.get("scientific_memory_commit")
        if isinstance(legacy_commit, str) and legacy_commit:
            return legacy_commit
    return None


def _write_canonical_import_report(release_dir: Path) -> None:
    import json

    report = dict(IMPORT_REPORT_TEMPLATE)
    commit = _resolve_scientific_memory_commit(release_dir)
    if commit:
        report["scientific_memory_commit"] = commit
        report["source_commit"] = commit
    report_path = release_dir / "scientific_memory_import_report.json"
    # release_manifest_hash is added during live import only (not part of manifest artifact hash).
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--release-dir", type=Path, default=DEFAULT_DIR)
    args = parser.parse_args()
    release_dir = args.release_dir.resolve()
    if not (release_dir / "RELEASE_FIXTURE_MANIFEST.json").is_file():
        print(f"error: missing legacy manifest in {release_dir}", file=sys.stderr)
        return 1

    sys.path.insert(0, str(REPO_ROOT / "pipeline" / "src"))
    from sm_pipeline.pcs_import.release_manifest_build import write_release_manifest
    from sm_pipeline.pcs_validate.release_chain_validation import validate_release_chain_validation
    from sm_pipeline.pcs_validate.release_manifest import validate_release_manifest

    release_run = (REPO_ROOT / "release-run").resolve()
    if release_dir.resolve() == release_run:
        _pin_scientific_memory_commit_in_legacy(release_dir)
    else:
        _pin_rc_fixture_commits(release_dir)
    _write_canonical_import_report(release_dir)

    if PCS_CORE_REGISTRY.is_file():
        VENDORED_REGISTRY_VALID.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(PCS_CORE_REGISTRY, VENDORED_REGISTRY_VALID)
        shutil.copy2(PCS_CORE_REGISTRY, VENDORED_REGISTRY_V0)
        shutil.copy2(PCS_CORE_REGISTRY, release_dir / "ArtifactRegistry.v0.json")
        print(f"copied pcs-core registry -> {VENDORED_REGISTRY_VALID}")

    if PCS_CORE_LABTRUST.is_dir():
        for handoff in sorted(PCS_CORE_LABTRUST.glob(HANDOFF_GLOB)):
            dest = release_dir / handoff.name
            shutil.copy2(handoff, dest)
            print(f"copied pcs-core handoff -> {dest}")

    pcs_labtrust = PCS_CORE_LABTRUST
    if _align_labtrust_gym_source_commits(release_dir):
        print(f"aligned LabTrust-Gym source commits in {release_dir}")
    if _align_labtrust_bundle_certificate_identity(release_dir):
        print(f"aligned certified/trace certificate identity in {release_dir}")
    if _sync_certified_bundle_hash_references(release_dir):
        print(f"synced certified bundle hash references in {release_dir}")
    _sync_legacy_manifest_producer_commits(release_dir)
    _sync_legacy_manifest_artifact_hashes(release_dir)

    out = write_release_manifest(release_dir)
    print(f"generated {out}")

    manifest_path = release_dir / "ReleaseManifest.v0.json"
    validation_path = release_dir / "ReleaseChainValidationResult.v0.json"
    if release_dir.resolve() != release_run:
        from sm_pipeline.pcs_import.pcs_core_release_align import align_scientific_memory_producer_repos
        from sm_pipeline.pcs_validate.canonical_hash import canonical_hash, file_sha256_digest

        manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
        aligned = align_scientific_memory_producer_repos(manifest, repo_root=REPO_ROOT)
        import_report_path = release_dir / "scientific_memory_import_report.json"
        artifacts = aligned.get("artifacts")
        if isinstance(artifacts, dict) and import_report_path.is_file():
            entry = dict(artifacts.get("scientific_memory_import_report.json") or {})
            entry["sha256"] = file_sha256_digest(import_report_path)
            artifacts["scientific_memory_import_report.json"] = entry
            aligned["artifacts"] = artifacts
        aligned["signature_or_digest"] = canonical_hash(
            {key: value for key, value in aligned.items() if key != "signature_or_digest"},
        )
        manifest_path.write_text(json.dumps(aligned, indent=2) + "\n", encoding="utf-8")

    if not validation_path.is_file():
        print(f"error: missing {validation_path}", file=sys.stderr)
        return 1

    if _align_release_chain_validation(validation_path):
        print(f"aligned release chain validation -> {validation_path}")

    manifest_errors = validate_release_manifest(manifest_path, repo_root=REPO_ROOT)
    if manifest_errors:
        for err in manifest_errors:
            print(f"error: manifest: {err}", file=sys.stderr)
        return 1

    manifest = __import__("json").loads(manifest_path.read_text(encoding="utf-8-sig"))
    validation_errors = validate_release_chain_validation(
        validation_path,
        repo_root=REPO_ROOT,
        expected_release_id=str(manifest.get("release_id") or ""),
    )
    if validation_errors:
        for err in validation_errors:
            print(f"error: validation: {err}", file=sys.stderr)
        return 1

    verify = REPO_ROOT / "scripts" / "verify_labtrust_release_fixture.py"
    if release_dir.resolve() == DEFAULT_DIR.resolve() and verify.is_file():
        import subprocess

        subprocess.run([sys.executable, str(verify), "--write"], cwd=REPO_ROOT, check=True)
        print(f"updated SM fixture manifest -> {release_dir / 'FIXTURE_MANIFEST.json'}")

    if release_dir.resolve() == DEFAULT_DIR.resolve():
        _mirror_fixture_tree_to_release_run()

    print(f"OK: Phase 2 fixtures valid in {release_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
