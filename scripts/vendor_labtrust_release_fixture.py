#!/usr/bin/env python3
"""Vendor PF signed bundle from provability-fabric labtrust-release fixtures."""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PF_LABTRUST_RELEASE = (
    REPO_ROOT.parent
    / "provability-fabric"
    / "tests"
    / "pcs"
    / "fixtures"
    / "labtrust-release"
    / "signed_science_claim_bundle.json"
)
LABTRUST_GYM_SIGNED = REPO_ROOT.parent / "LabTrust-Gym" / "signed_science_claim_bundle.json"
DEST_DIR = REPO_ROOT / "tests" / "pcs" / "fixtures" / "labtrust-release"
DEST = DEST_DIR / "signed_science_claim_bundle.json"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--signed",
        type=Path,
        help="Override signed_science_claim_bundle.json source",
    )
    parser.add_argument(
        "--copy-all",
        action="store_true",
        help="Copy entire provability-fabric labtrust-release fixture directory",
    )
    args = parser.parse_args()
    if args.signed is not None:
        source = args.signed.resolve()
    elif PF_LABTRUST_RELEASE.is_file():
        source = PF_LABTRUST_RELEASE
    elif LABTRUST_GYM_SIGNED.is_file():
        source = LABTRUST_GYM_SIGNED
    else:
        print(
            "skip: no PF fixture at provability-fabric/tests/pcs/fixtures/labtrust-release/",
            file=sys.stderr,
        )
        return 0
    DEST_DIR.mkdir(parents=True, exist_ok=True)
    if args.copy_all and PF_LABTRUST_RELEASE.parent.is_dir():
        for path in PF_LABTRUST_RELEASE.parent.iterdir():
            if path.is_file() and path.name not in ("FIXTURE_SOURCE.md",):
                shutil.copy2(path, DEST_DIR / path.name)
        print(f"fixtures -> {DEST_DIR} (from {PF_LABTRUST_RELEASE.parent})")
    else:
        shutil.copy2(source, DEST)
        print(f"fixture -> {DEST} (from {source})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
