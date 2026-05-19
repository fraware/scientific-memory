"""Formal trust kernel import, read model, query, and strict validation."""

from __future__ import annotations

import json
import shutil
import tempfile
from pathlib import Path

import pytest

from sm_pipeline.pcs_import.formal_trust_protocol import FORMAL_NON_CLAIMS, MILESTONE_THEOREMS
from sm_pipeline.pcs_import.release_manifest_importer import import_release_manifest
from sm_pipeline.pcs_validate.formal_trust_validation import require_formal_trust_artifacts
from sm_pipeline.pcs_validate.validator import BundleValidationError

from schema_fixtures import (
    EXPECTED_LABTRUST_CLAIM_ID,
    LABTRUST_RELEASE_DIR,
    LABTRUST_RELEASE_MANIFEST_V0,
    copy_pcs_schemas,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
LABTRUST_MANIFEST = LABTRUST_RELEASE_MANIFEST_V0


def test_labtrust_fixture_has_formal_trust_artifacts() -> None:
    assert (LABTRUST_RELEASE_DIR / "proof_obligation.v0.json").is_file()
    assert (LABTRUST_RELEASE_DIR / "lean_check_result.v0.json").is_file()


def test_require_formal_trust_passes_on_labtrust_fixture() -> None:
    manifest = json.loads(LABTRUST_MANIFEST.read_text(encoding="utf-8-sig"))
    from sm_pipeline.pcs_import.workflow_profile import load_workflow_profile

    profile = load_workflow_profile(str(manifest["workflow_profile_id"]), repo_root=REPO_ROOT)
    obligation, lean = require_formal_trust_artifacts(
        LABTRUST_RELEASE_DIR,
        manifest,
        repo_root=REPO_ROOT,
        workflow_profile=profile,
    )
    assert obligation["release_id"] == manifest["release_id"]
    assert lean["status"] == "ProofChecked"
    assert len(obligation["obligations"]) == len(MILESTONE_THEOREMS)


def test_import_rejects_missing_proof_obligation() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        copy_pcs_schemas(root)
        release_dir = root / "labtrust-release"
        shutil.copytree(LABTRUST_RELEASE_DIR, release_dir)
        (release_dir / "proof_obligation.v0.json").unlink()
        with pytest.raises(BundleValidationError, match="ProofObligation|proof_obligation"):
            import_release_manifest(release_dir / "ReleaseManifest.v0.json", repo_root=root, render=False)


def test_import_rejects_failed_lean_check() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        copy_pcs_schemas(root)
        release_dir = root / "labtrust-release"
        shutil.copytree(LABTRUST_RELEASE_DIR, release_dir)
        lean_path = release_dir / "lean_check_result.v0.json"
        lean = json.loads(lean_path.read_text(encoding="utf-8-sig"))
        lean["status"] = "Rejected"
        lean["results"][0]["status"] = "Rejected"
        lean["results"][0]["result"] = "failed"
        sys_path = REPO_ROOT / "pipeline" / "src"
        import sys

        sys.path.insert(0, str(sys_path))
        from sm_pipeline.pcs_validate.canonical_hash import canonical_hash

        lean["signature_or_digest"] = canonical_hash(lean)
        lean_path.write_text(json.dumps(lean, indent=2) + "\n", encoding="utf-8")
        manifest_path = release_dir / "ReleaseManifest.v0.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
        from sm_pipeline.pcs_validate.canonical_hash import file_sha256_digest

        artifacts = manifest.get("artifacts")
        if isinstance(artifacts, dict):
            entry = dict(artifacts.get("lean_check_result.v0.json") or {})
            entry["sha256"] = file_sha256_digest(lean_path)
            artifacts["lean_check_result.v0.json"] = entry
            manifest["artifacts"] = artifacts
            manifest["signature_or_digest"] = canonical_hash(
                {k: v for k, v in manifest.items() if k != "signature_or_digest"},
            )
            manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        with pytest.raises(BundleValidationError, match="ProofChecked|failed obligation"):
            import_release_manifest(release_dir / "ReleaseManifest.v0.json", repo_root=root, render=False)


def test_import_populates_formal_trust_read_model() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        copy_pcs_schemas(root)
        release_dir = root / "labtrust-release"
        shutil.copytree(LABTRUST_RELEASE_DIR, release_dir)
        import_release_manifest(release_dir / "ReleaseManifest.v0.json", repo_root=root, render=False)
        read_model = json.loads(
            (root / "corpus" / "pcs" / "claims" / EXPECTED_LABTRUST_CLAIM_ID / "read_model.json").read_text(
                encoding="utf-8",
            ),
        )
        kernel = read_model.get("formal_trust_kernel")
        assert isinstance(kernel, dict)
        assert kernel.get("title") == "Formal Trust Kernel"
        assert kernel.get("formal_non_claims") == list(FORMAL_NON_CLAIMS)
        assert len(kernel.get("lean_check_results") or []) == len(MILESTONE_THEOREMS)


def test_show_formal_checks_cli_payload() -> None:
    from sm_pipeline.pcs_import.claim_index import write_claims_index
    from sm_pipeline.pcs_import.claim_query import show_formal_checks

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        copy_pcs_schemas(root)
        release_dir = root / "labtrust-release"
        shutil.copytree(LABTRUST_RELEASE_DIR, release_dir)
        import_release_manifest(release_dir / "ReleaseManifest.v0.json", repo_root=root, render=False)
        write_claims_index(root)
        payload = show_formal_checks(root, EXPECTED_LABTRUST_CLAIM_ID)
        assert payload["claim_id"] == EXPECTED_LABTRUST_CLAIM_ID
        assert isinstance(payload.get("formal_trust_kernel"), dict)
        assert payload["formal_trust_kernel"].get("formal_non_claims") == list(FORMAL_NON_CLAIMS)


def test_list_formal_check_queries() -> None:
    from sm_pipeline.pcs_import.claim_index import write_claims_index
    from sm_pipeline.pcs_import.claim_query import (
        list_claims_with_failed_formal_checks,
        list_claims_with_formal_checks,
    )

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        copy_pcs_schemas(root)
        release_dir = root / "labtrust-release"
        shutil.copytree(LABTRUST_RELEASE_DIR, release_dir)
        import_release_manifest(release_dir / "ReleaseManifest.v0.json", repo_root=root, render=False)
        write_claims_index(root)
        with_formal = list_claims_with_formal_checks(root)
        assert EXPECTED_LABTRUST_CLAIM_ID in with_formal
        failed = list_claims_with_failed_formal_checks(root)
        assert EXPECTED_LABTRUST_CLAIM_ID not in failed


def test_query_by_lean_theorem() -> None:
    from sm_pipeline.pcs_import.claim_index import write_claims_index
    from sm_pipeline.pcs_import.claim_query import list_claims_by_lean_theorem

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        copy_pcs_schemas(root)
        release_dir = root / "labtrust-release"
        shutil.copytree(LABTRUST_RELEASE_DIR, release_dir)
        import_release_manifest(release_dir / "ReleaseManifest.v0.json", repo_root=root, render=False)
        write_claims_index(root)
        matches = list_claims_by_lean_theorem(root, "PCS.CertificateMatchesRuntime")
        assert EXPECTED_LABTRUST_CLAIM_ID in matches
