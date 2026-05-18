"""Copy PCS schema mirrors into a temp repo root for isolated tests."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURES = Path(__file__).resolve().parent / "fixtures"


def pcs_subprocess_python() -> str:
    """Prefer project venv Python (typer>=0.12) over bare system interpreters."""
    for candidate in (
        REPO_ROOT / ".venv" / "Scripts" / "python.exe",
        REPO_ROOT / ".venv" / "bin" / "python",
    ):
        if candidate.is_file():
            return str(candidate)
    return sys.executable


def pcs_cli_env(*, repo_root: Path | None = None) -> dict[str, str]:
    env = os.environ.copy()
    root = (repo_root or REPO_ROOT).resolve()
    env["PYTHONPATH"] = str(REPO_ROOT / "pipeline" / "src")
    prefix = env.get("PYTHONPATH", "")
    if prefix and str(REPO_ROOT / "pipeline" / "src") not in prefix.split(os.pathsep):
        env["PYTHONPATH"] = str(REPO_ROOT / "pipeline" / "src") + os.pathsep + prefix
    env["SCIENTIFIC_MEMORY_REPO_ROOT"] = str(root)
    pcs_core = resolve_pcs_core_root()
    if pcs_core.is_dir():
        env["PCS_CORE_PATH"] = str(pcs_core)
    return env


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
LABTRUST_RELEASE_MANIFEST_V0 = FIXTURES / "labtrust-release" / "ReleaseManifest.v0.json"
LABTRUST_RELEASE_CHAIN_VALIDATION = (
    FIXTURES / "labtrust-release" / "ReleaseChainValidationResult.v0.json"
)
LABTRUST_RELEASE_DIR = FIXTURES / "labtrust-release"
TOOL_USE_RELEASE_DIR = FIXTURES / "tool-use-release"
TOOL_USE_RELEASE_MANIFEST = TOOL_USE_RELEASE_DIR / "release_manifest.v0.json"
TOOL_USE_WORKFLOW_ID = "agent_tool_use.safety_v0"
TOOL_USE_RELEASE_ID = "release-pcs-v0.1-tool-use-safety"
SM_FIXTURE_MANIFEST = FIXTURES / "labtrust-release" / "FIXTURE_MANIFEST.json"
EXPECTED_LABTRUST_CLAIM_ID = "claim-pcs-qc-release-v0.1"

# Canonical RC chain: pcs-core/examples/labtrust-release/ (single source of truth).
PCS_CORE_CANONICAL_RELEASE = resolve_pcs_core_root() / "examples" / "labtrust-release"
PCS_CORE_CANONICAL_SIGNED_BUNDLE = PCS_CORE_CANONICAL_RELEASE / "signed_science_claim_bundle.json"


def _labtrust_fixture_rc_chain_ids() -> tuple[str, str, str]:
    """certificate_id, trace_hash, certified_bundle manifest hash from committed labtrust fixture."""
    fixture_dir = FIXTURES / "labtrust-release"
    signed_path = fixture_dir / "signed_science_claim_bundle.json"
    trace_path = fixture_dir / "trace.json"
    manifest_path = fixture_dir / "RELEASE_FIXTURE_MANIFEST.json"
    if not (signed_path.is_file() and trace_path.is_file() and manifest_path.is_file()):
        return (
            "cert-trace-a1b8ff9d-7d5f-489c-98b1-a3a630cb87d7",
            "sha256:c3e8a3dc4ad86d533de1dfa4ae7fe2a338c2cff3c945404c96a75216524d58cd",
            "sha256:bb740698a01c4e918ca0f346e5bfaed83e6665da8df84e931c0d50e03ce82ffe",
        )
    signed = json.loads(signed_path.read_text(encoding="utf-8"))
    trace = json.loads(trace_path.read_text(encoding="utf-8"))
    manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    cert_id = signed["science_claim_bundle"]["certificates"][0]["certificate_id"]
    trace_hash = trace["trace_hash"]
    certified_hash = manifest["artifacts"]["science_claim_bundle.certified.json"]
    return cert_id, trace_hash, certified_hash


(
    CANONICAL_RC_CERTIFICATE_ID,
    CANONICAL_RC_TRACE_HASH,
    CANONICAL_RC_CERTIFIED_BUNDLE_HASH,
) = _labtrust_fixture_rc_chain_ids()
def _labtrust_fixture_producer_commits() -> tuple[str, str, str, str]:
    """labtrust_gym, certifyedge, provability_fabric, pcs_core from committed legacy manifest."""
    manifest_path = FIXTURES / "labtrust-release" / "RELEASE_FIXTURE_MANIFEST.json"
    if not manifest_path.is_file():
        return (
            "17ed831acfd775889ab497d11004cceb083a9c2d",
            "635fca3771ad54fe3f8b49d1bb77ee35d0680ddc",
            "0f659b90c80c46a6bbfd51b0d37ea723b032fb9d",
            "17e414501b3e1c58e8fbde1fe89a828440a945d9",
        )
    manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    return (
        manifest["labtrust_gym_commit"],
        manifest["certifyedge_commit"],
        manifest["provability_fabric_commit"],
        manifest["pcs_core_commit"],
    )


(
    CANONICAL_RC_LABTRUST_COMMIT,
    CANONICAL_RC_CERTIFYEDGE_COMMIT,
    CANONICAL_RC_PF_COMMIT,
    CANONICAL_RC_PCS_CORE_COMMIT,
) = _labtrust_fixture_producer_commits()
# Scientific Memory commit published in pcs-core labtrust release manifest (fallback when pcs-core absent).
_CANONICAL_RC_SCIENTIFIC_MEMORY_COMMIT_FALLBACK = "0e059e934bc95bcc4dc0cb6593b18b07a28529a2"


def canonical_rc_scientific_memory_commit() -> str:
    """Match pcs-core/examples/labtrust-release release_manifest.v0.json when available."""
    sys.path.insert(0, str(REPO_ROOT / "pipeline" / "src"))
    from sm_pipeline.pcs_import.pcs_core_release_align import pcs_core_scientific_memory_commit

    return pcs_core_scientific_memory_commit(REPO_ROOT) or _CANONICAL_RC_SCIENTIFIC_MEMORY_COMMIT_FALLBACK


CANONICAL_RC_SCIENTIFIC_MEMORY_COMMIT = canonical_rc_scientific_memory_commit()


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
