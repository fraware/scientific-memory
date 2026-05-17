#!/usr/bin/env python3
"""Vendor PCS v0.1 labtrust-release fixtures from pcs-core (release provenance)."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DEST_DIR = REPO_ROOT / "tests" / "pcs" / "fixtures" / "labtrust-release"
PCS_CORE_RELEASE = REPO_ROOT.parent / "pcs-core" / "examples" / "labtrust-release"
PF_LABTRUST_RELEASE = (
    REPO_ROOT.parent
    / "provability-fabric"
    / "tests"
    / "pcs"
    / "fixtures"
    / "labtrust-release"
)
SKIP_COPY = frozenset({"FIXTURE_SOURCE.md", "FIXTURE_MANIFEST.json"})
RELEASE_MANIFEST_NAME = "RELEASE_FIXTURE_MANIFEST.json"
MANIFEST_ARTIFACTS = (
    "trace.json",
    "runtime_receipt.json",
    "trace_certificate.json",
    "science_claim_bundle.pending.json",
    "science_claim_bundle.certified.json",
    "verification_result.json",
    "signed_science_claim_bundle.json",
    "scientific_memory_import_report.json",
)


def _sha256(path: Path) -> str:
    return f"sha256:{hashlib.sha256(path.read_bytes()).hexdigest()}"


def _refresh_release_manifest_hashes(release_dir: Path) -> None:
    manifest_path = release_dir / RELEASE_MANIFEST_NAME
    if not manifest_path.is_file():
        return
    manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    artifacts: dict[str, str] = {}
    for name in MANIFEST_ARTIFACTS:
        path = release_dir / name
        if path.is_file():
            artifacts[name] = _sha256(path)
    manifest["artifacts"] = artifacts
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def _align_pf_provenance(signed: dict, pf_commit: str) -> None:
    """Set PF wrapper + verification_result source_commit to manifest pin."""
    vr = signed.get("verification_result")
    if isinstance(vr, dict):
        vr["source_commit"] = pf_commit
        vr.setdefault("source_repo", "https://github.com/SentinelOps-CI/provability-fabric")
    signed["source_commit"] = pf_commit
    signed.setdefault("source_repo", "https://github.com/SentinelOps-CI/provability-fabric")


def _load_manifest(release_dir: Path) -> dict:
    path = release_dir / "RELEASE_FIXTURE_MANIFEST.json"
    if not path.is_file():
        raise FileNotFoundError(f"missing {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def vendor_from_release_dir(source_dir: Path, *, align_pf: bool = True) -> None:
    DEST_DIR.mkdir(parents=True, exist_ok=True)
    manifest = _load_manifest(source_dir)
    pf_commit = str(manifest.get("provability_fabric_commit") or "").strip()
    if len(pf_commit) != 40:
        raise ValueError("RELEASE_FIXTURE_MANIFEST.json: invalid provability_fabric_commit")

    for path in source_dir.iterdir():
        if not path.is_file() or path.name in SKIP_COPY:
            continue
        shutil.copy2(path, DEST_DIR / path.name)

    signed_path = DEST_DIR / "signed_science_claim_bundle.json"
    signed = json.loads(signed_path.read_text(encoding="utf-8"))
    if align_pf:
        _align_pf_provenance(signed, pf_commit)
        signed_path.write_text(json.dumps(signed, indent=2) + "\n", encoding="utf-8")
        vr_path = DEST_DIR / "verification_result.json"
        if vr_path.is_file():
            vr = json.loads(vr_path.read_text(encoding="utf-8"))
            if isinstance(vr, dict):
                vr["source_commit"] = pf_commit
                vr.setdefault(
                    "source_repo", "https://github.com/SentinelOps-CI/provability-fabric"
                )
                vr_path.write_text(json.dumps(vr, indent=2) + "\n", encoding="utf-8")

    # Ship pcs-core release manifest for manifest-aware import tests.
    shutil.copy2(
        source_dir / RELEASE_MANIFEST_NAME,
        DEST_DIR / RELEASE_MANIFEST_NAME,
    )
    _refresh_release_manifest_hashes(DEST_DIR)
    print(f"fixtures -> {DEST_DIR} (from {source_dir})")
    print(f"  provability_fabric_commit={pf_commit}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source",
        type=Path,
        help="Override release directory (default: pcs-core/examples/labtrust-release)",
    )
    parser.add_argument(
        "--no-align-pf",
        action="store_true",
        help="Do not rewrite PF source_commit fields from manifest",
    )
    args = parser.parse_args()
    source = (args.source or PCS_CORE_RELEASE).resolve()
    if not (source / "signed_science_claim_bundle.json").is_file():
        if (PF_LABTRUST_RELEASE.parent / "signed_science_claim_bundle.json").is_file():
            print(
                "warning: pcs-core release dir missing; falling back to provability-fabric",
                file=sys.stderr,
            )
            for path in PF_LABTRUST_RELEASE.parent.iterdir():
                if path.is_file() and path.name not in SKIP_COPY:
                    shutil.copy2(path, DEST_DIR / path.name)
            print(f"fixtures -> {DEST_DIR} (from {PF_LABTRUST_RELEASE.parent})")
            return 0
        print(f"error: no release fixtures at {source}", file=sys.stderr)
        return 1
    vendor_from_release_dir(source, align_pf=not args.no_align_pf)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
