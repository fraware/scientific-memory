#!/usr/bin/env python3
"""Populate scientific-memory/release-run/ from one LabTrust-Gym chain workdir."""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_WORK = REPO_ROOT.parent / "LabTrust-Gym"
DEFAULT_RUN = REPO_ROOT / "release-run"

CHAIN_FILES = (
    "trace.json",
    "runtime_receipt.json",
    "trace_certificate.json",
    "science_claim_bundle.pending.json",
    "science_claim_bundle.certified.json",
    "verification_result.json",
    "signed_science_claim_bundle.json",
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workdir", type=Path, default=DEFAULT_WORK)
    parser.add_argument("--run-dir", type=Path, default=DEFAULT_RUN)
    parser.add_argument("--use-pcs-core", action="store_true", default=True)
    args = parser.parse_args()

    work = args.workdir.resolve()
    run_dir = args.run_dir.resolve()

    missing = [name for name in CHAIN_FILES if not (work / name).is_file()]
    if missing:
        print(f"error: workdir missing chain artifacts: {', '.join(missing)}", file=sys.stderr)
        return 1

    if args.use_pcs_core:
        try:
            from pcs_core.release_fixtures import build_release_run

            path = build_release_run(work, run_dir=run_dir)
            print(f"release-run -> {path} (pcs-core build_release_run)")
            return 0
        except ImportError:
            print("pcs-core not installed; using file copy only", file=sys.stderr)

    if run_dir.exists():
        shutil.rmtree(run_dir)
    run_dir.mkdir(parents=True)
    for name in CHAIN_FILES:
        shutil.copy2(work / name, run_dir / name)
    print(f"release-run -> {run_dir} (chain copy; run import-release-run next)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
