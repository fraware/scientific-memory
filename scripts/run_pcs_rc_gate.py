#!/usr/bin/env python3
"""Cross-platform PCS RC + Phase 2 gate (same checks as run_pcs_rc_ci_gate.sh)."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PIPELINE_SRC = REPO_ROOT / "pipeline" / "src"


def _python() -> str:
    for candidate in (
        REPO_ROOT / ".venv" / "Scripts" / "python.exe",
        REPO_ROOT / ".venv" / "bin" / "python",
    ):
        if candidate.is_file():
            return str(candidate)
    return sys.executable


def _node() -> str:
    env_node = os.environ.get("NODE", "").strip()
    if env_node:
        return env_node
    found = shutil.which("node")
    return found if found else "node"


def _run_portal_pcs_contracts() -> None:
    """Run portal zod contract scripts (no pnpm required)."""
    portal = REPO_ROOT / "portal"
    if not (portal / "node_modules" / "zod").is_dir():
        print(
            "error: portal node_modules missing; run: cd portal && npm install",
            file=sys.stderr,
        )
        raise SystemExit(1)
    node = _node()
    contract_runs = (
        ["scripts/verify-pcs-read-model.mjs"],
        [
            "scripts/verify-pcs-phase2-read-model.mjs",
            "../corpus/pcs/claims/claim-pcs-qc-release-v0.1/read_model.json",
        ],
        [
            "scripts/verify-pcs-phase2-read-model.mjs",
            "../tests/pcs/fixtures/tool-use-release/.phase2-read-model.json",
        ],
        [
            "scripts/verify-pcs-phase2-read-model.mjs",
            "../tests/pcs/fixtures/computation-release/.phase2-read-model.json",
        ],
        [
            "scripts/verify-pcs-phase2-read-model.mjs",
            "../tests/pcs/fixtures/computation-rejected-release/.phase2-read-model.json",
        ],
    )
    for parts in contract_runs:
        _run([node, *parts], cwd=portal)


def _run(cmd: list[str], *, cwd: Path | None = None, env: dict[str, str] | None = None) -> None:
    merged = os.environ.copy()
    if env:
        merged.update(env)
    merged["PYTHONPATH"] = str(PIPELINE_SRC) + (
        os.pathsep + merged["PYTHONPATH"] if merged.get("PYTHONPATH") else ""
    )
    print("==>", " ".join(cmd))
    if cmd and cmd[0] == sys.executable:
        cmd = [_python(), *cmd[1:]]
    subprocess.run(cmd, cwd=cwd or REPO_ROOT, env=merged, check=True)


def main() -> int:
    pcs_core = REPO_ROOT / "pcs-core"
    if not (pcs_core / "examples" / "labtrust-release").is_dir():
        sibling = REPO_ROOT.parent / "pcs-core"
        if (sibling / "examples" / "labtrust-release").is_dir():
            pcs_core = sibling
    env = {"PCS_CORE_PATH": str(pcs_core)} if pcs_core.is_dir() else {}

    _run([sys.executable, str(REPO_ROOT / "scripts" / "ensure_labtrust_phase2_fixtures.py")], env=env)

    _run(
        [sys.executable, str(REPO_ROOT / "scripts" / "sync_labtrust_release_from_pcs_core.py"), "--no-corpus"],
        env=env,
    )

    fixture_bundle = REPO_ROOT / "tests/pcs/fixtures/labtrust-release/signed_science_claim_bundle.json"
    pcs_bundle = pcs_core / "examples/labtrust-release/signed_science_claim_bundle.json"
    if pcs_bundle.is_file() and fixture_bundle.read_bytes() != pcs_bundle.read_bytes():
        print("error: signed bundle drifted from pcs-core", file=sys.stderr)
        return 1

    pcs_labtrust = pcs_core / "examples/labtrust-release"
    manifest_example = None
    for name in ("release_manifest.v0.json", "ReleaseManifest.v0.json"):
        candidate = pcs_labtrust / name
        if candidate.is_file():
            manifest_example = candidate
            break
    if manifest_example is not None:
        sm_manifest = json.loads(
            (REPO_ROOT / "tests/pcs/fixtures/labtrust-release/ReleaseManifest.v0.json").read_text(
                encoding="utf-8-sig",
            ),
        )
        pcs_manifest = json.loads(manifest_example.read_text(encoding="utf-8-sig"))
        key = "signed_science_claim_bundle.json"
        if sm_manifest["artifacts"][key]["sha256"] != pcs_manifest["artifacts"][key]["sha256"]:
            print("ReleaseManifest signed bundle hash mismatch vs pcs-core", file=sys.stderr)
            return 1
        print("OK: ReleaseManifest signed bundle hash matches pcs-core labtrust release")

    manifest = REPO_ROOT / "tests/pcs/fixtures/labtrust-release/ReleaseManifest.v0.json"
    _run(
        [
            sys.executable,
            "-m",
            "sm_pipeline.cli",
            "pcs-import-release",
            "--release-manifest",
            str(manifest.relative_to(REPO_ROOT)),
        ],
        env=env,
    )

    _run([sys.executable, str(REPO_ROOT / "scripts" / "verify_tool_use_release_fixture.py")], env=env)

    computation_manifest = (
        REPO_ROOT / "tests/pcs/fixtures/computation-release/release_manifest.v0.json"
    )
    if computation_manifest.is_file():
        _run(
            [sys.executable, str(REPO_ROOT / "scripts" / "verify_computation_release_fixture.py")],
            env=env,
        )
        _run(
            [
                sys.executable,
                "-m",
                "sm_pipeline.cli",
                "pcs-import-release",
                "--release-manifest",
                str(computation_manifest.relative_to(REPO_ROOT)),
            ],
            env=env,
        )
    else:
        print(
            "warn: computation-release fixtures missing; run: just bootstrap-computation-release",
            file=sys.stderr,
        )

    _run([sys.executable, "-m", "pytest", str(REPO_ROOT / "tests/pcs"), "-q"], env=env)
    _run(
        [
            sys.executable,
            "-m",
            "sm_pipeline.cli",
            "pcs-render-claim",
            "--claim-id",
            "claim-pcs-qc-release-v0.1",
        ],
        env=env,
    )

    report_path = (
        REPO_ROOT
        / "corpus/pcs/claims/claim-pcs-qc-release-v0.1/scientific_memory_import_report.json"
    )
    report = json.loads(report_path.read_text(encoding="utf-8"))
    required = (
        "release_chain_validation_id",
        "release_chain_validation_status",
        "release_chain_validator",
        "release_chain_checked_at",
        "release_manifest_hash",
        "signed_bundle_hash",
        "certificate_id",
        "trace_hash",
        "artifact_registry_version",
    )
    missing = [key for key in required if key not in report]
    if missing:
        print("missing import report keys:", ", ".join(missing), file=sys.stderr)
        return 1
    if report.get("release_chain_validation_status") != "ProofChecked":
        print("expected ProofChecked release chain status", file=sys.stderr)
        return 1

    _run_portal_pcs_contracts()

    index_path = REPO_ROOT / "corpus/pcs/claims_index.json"
    if not index_path.is_file():
        print("missing corpus/pcs/claims_index.json", file=sys.stderr)
        return 1

    print("OK: PCS RC + Phase 2 gate passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
