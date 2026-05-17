#!/usr/bin/env python3
"""Atomically promote release-run/ to test fixtures (after chain validation)."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RUN = REPO_ROOT / "release-run"
FIXTURE_DIR = REPO_ROOT / "tests" / "pcs" / "fixtures" / "labtrust-release"
PCS_CORE_RELEASE = REPO_ROOT.parent / "pcs-core" / "examples" / "labtrust-release"
MANIFEST_NAME = "RELEASE_FIXTURE_MANIFEST.json"
MANIFEST_ARTIFACTS = (
    "trace.json",
    "runtime_receipt.json",
    "trace_certificate.json",
    "science_claim_bundle.pending.json",
    "science_claim_bundle.certified.json",
    "verification_result.json",
    "signed_science_claim_bundle.json",
    "scientific_memory_import_report.json",
    MANIFEST_NAME,
)
PRESERVE_GLOBS = ("invalid_*.json", "missing_claim_*.json", "FIXTURE_*.md")


def _sha256(path: Path) -> str:
    return f"sha256:{hashlib.sha256(path.read_bytes()).hexdigest()}"


def _refresh_manifest_hashes(run_dir: Path) -> None:
    manifest_path = run_dir / MANIFEST_NAME
    if not manifest_path.is_file():
        return
    manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    manifest["artifacts"] = {
        name: _sha256(run_dir / name)
        for name in MANIFEST_ARTIFACTS
        if name != MANIFEST_NAME and (run_dir / name).is_file()
    }
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def promote(run_dir: Path, *, target: Path, pcs_core: bool) -> None:
    sys.path.insert(0, str(REPO_ROOT / "pipeline" / "src"))
    from sm_pipeline.pcs_validate.release_chain import validate_release_chain

    issues = validate_release_chain(run_dir)
    if issues:
        for issue in issues:
            print(f"error: {issue.format()}", file=sys.stderr)
        raise SystemExit(1)

    target.mkdir(parents=True, exist_ok=True)

    for name in MANIFEST_ARTIFACTS:
        src = run_dir / name
        if not src.is_file():
            print(f"error: release-run missing {name}", file=sys.stderr)
            raise SystemExit(1)
        shutil.copy2(src, target / name)

    print(f"promoted {run_dir} -> {target}")

    if pcs_core:
        PCS_CORE_RELEASE.mkdir(parents=True, exist_ok=True)
        for name in MANIFEST_ARTIFACTS:
            shutil.copy2(run_dir / name, PCS_CORE_RELEASE / name)
        print(f"promoted {run_dir} -> {PCS_CORE_RELEASE}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path, default=DEFAULT_RUN)
    parser.add_argument("--target", type=Path, default=FIXTURE_DIR)
    parser.add_argument("--pcs-core", action="store_true", help="Also promote to pcs-core/examples")
    parser.add_argument("--refresh-hashes", action="store_true")
    args = parser.parse_args()
    run_dir = args.run_dir.resolve()
    if not (run_dir / "signed_science_claim_bundle.json").is_file():
        print(f"error: incomplete release-run at {run_dir}", file=sys.stderr)
        return 1
    if args.refresh_hashes:
        _refresh_manifest_hashes(run_dir)
    promote(run_dir, target=args.target.resolve(), pcs_core=args.pcs_core)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
