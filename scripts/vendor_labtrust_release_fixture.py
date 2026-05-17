#!/usr/bin/env python3
"""Copy PF signed bundle from LabTrust-Gym clean-checkout chain into test fixtures."""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = REPO_ROOT.parent / "LabTrust-Gym" / "signed_science_claim_bundle.json"
DEST = REPO_ROOT / "tests" / "pcs" / "fixtures" / "labtrust-release" / "signed_science_claim_bundle.json"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--signed",
        type=Path,
        default=DEFAULT_SOURCE,
        help="signed_science_claim_bundle.json from pf sign (LabTrust-Gym workdir)",
    )
    args = parser.parse_args()
    source = args.signed.resolve()
    if not source.is_file():
        print(f"skip: no signed bundle at {source} (run LabTrust-Gym clean chain to refresh)")
        return 0
    DEST.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, DEST)
    print(f"fixture -> {DEST}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
