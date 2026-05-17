"""Copy PCS schema mirrors into a temp repo root for isolated tests."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURES = Path(__file__).resolve().parent / "fixtures"


def resolve_pcs_core_root() -> Path:
    """pcs-core root: PCS_CORE_PATH, ./pcs-core (CI), or ../pcs-core (local sibling)."""
    if env := os.environ.get("PCS_CORE_PATH", "").strip():
        return Path(env).resolve()
    in_repo = REPO_ROOT / "pcs-core"
    if (in_repo / "examples" / "labtrust-release").is_dir():
        return in_repo
    return (REPO_ROOT.parent / "pcs-core").resolve()


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

# PF release bundle: provability-fabric/tests/pcs/fixtures/labtrust-release/ (pf sign).
LABTRUST_RELEASE_BUNDLE = FIXTURES / "labtrust-release" / "signed_science_claim_bundle.json"
LABTRUST_RELEASE_CERTIFIED = FIXTURES / "labtrust-release" / "science_claim_bundle.certified.json"
LABTRUST_RELEASE_IMPORT_REPORT = (
    FIXTURES / "labtrust-release" / "scientific_memory_import_report.json"
)
LABTRUST_RELEASE_MANIFEST = FIXTURES / "labtrust-release" / "RELEASE_FIXTURE_MANIFEST.json"
SM_FIXTURE_MANIFEST = FIXTURES / "labtrust-release" / "FIXTURE_MANIFEST.json"
EXPECTED_LABTRUST_CLAIM_ID = "claim-pcs-qc-release-v0.1"

# Canonical RC chain: pcs-core/examples/labtrust-release/ (single source of truth).
PCS_CORE_CANONICAL_RELEASE = resolve_pcs_core_root() / "examples" / "labtrust-release"
PCS_CORE_CANONICAL_SIGNED_BUNDLE = PCS_CORE_CANONICAL_RELEASE / "signed_science_claim_bundle.json"
CANONICAL_RC_CERTIFICATE_ID = "cert-trace-886c95f0-5d63-42d6-aa13-5891c12c5a6a"
CANONICAL_RC_TRACE_HASH = "sha256:c3e8a3dc4ad86d533de1dfa4ae7fe2a338c2cff3c945404c96a75216524d58cd"
CANONICAL_RC_CERTIFIED_BUNDLE_HASH = (
    "sha256:9b42d792199eb6f358d26f822699f0ed65bb4366eee306d4958d42121c656833"
)
CANONICAL_RC_LABTRUST_COMMIT = "4c5439ae358733f9a4c4a58e33fdaed1ab0d29de"
CANONICAL_RC_CERTIFYEDGE_COMMIT = "cb6848001e2e60a484e04eba5ad6be3fe2e4eccc"
CANONICAL_RC_PF_COMMIT = "0f659b90c80c46a6bbfd51b0d37ea723b032fb9d"
# Scientific Memory commit pinned in vendored import report (synced from pcs-core RC).
def _fixture_scientific_memory_commit() -> str:
    if LABTRUST_RELEASE_IMPORT_REPORT.is_file():
        report = json.loads(LABTRUST_RELEASE_IMPORT_REPORT.read_text(encoding="utf-8-sig"))
        commit = report.get("scientific_memory_commit")
        if isinstance(commit, str) and len(commit) == 40:
            return commit
    return "5b4b81049b430d1b59ff5b51f688eb0feaeef76c"


CANONICAL_RC_SCIENTIFIC_MEMORY_COMMIT = _fixture_scientific_memory_commit()

# Canonical import/render tests use the LabTrust v0.1 release fixture (synced from pcs-core).
PF_SIGNED_BUNDLE = LABTRUST_RELEASE_BUNDLE
LEGACY_SIGNED_BUNDLE = FIXTURES / "valid_signed_science_claim_bundle.json"

IMPORT_REPORT_REQUIRED_KEYS = frozenset(
    {
        "claim_id",
        "verification_status",
        "warnings",
        "stale_artifacts",
        "render_path",
    }
)


def copy_pcs_schemas(root: Path) -> None:
    dest = root / "schemas" / "pcs"
    dest.mkdir(parents=True, exist_ok=True)
    src = REPO_ROOT / "schemas" / "pcs"
    for f in src.glob("*.json"):
        shutil.copy(f, dest / f.name)
    legacy_dest = dest / "legacy"
    legacy_dest.mkdir(exist_ok=True)
    for f in src.glob("legacy/*.json"):
        shutil.copy(f, legacy_dest / f.name)
