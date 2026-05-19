#!/usr/bin/env python3
"""Publish SM computation-release examples to adjacent pcs-core (maintainer workflow)."""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SOURCE = REPO_ROOT / "examples" / "computation-release"
DEFAULT_PCS_CORE = REPO_ROOT.parent / "pcs-core" / "examples" / "computation-release"
REJECTED_SOURCE = REPO_ROOT / "tests" / "pcs" / "fixtures" / "computation-rejected-release"
DEFAULT_PCS_CORE_REJECTED = (
    REPO_ROOT.parent / "pcs-core" / "examples" / "computation-rejected-release"
)


def _copy_tree(src: Path, dest: Path) -> None:
    if not src.is_dir():
        print(f"error: missing {src}", file=sys.stderr)
        raise SystemExit(1)
    dest.mkdir(parents=True, exist_ok=True)
    for path in sorted(src.iterdir()):
        if path.is_file() and not path.name.startswith("."):
            shutil.copy2(path, dest / path.name)
    print(f"published {src.name} -> {dest}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pcs-core-dir", type=Path, default=DEFAULT_PCS_CORE)
    parser.add_argument(
        "--pcs-core-rejected-dir",
        type=Path,
        default=DEFAULT_PCS_CORE_REJECTED,
    )
    parser.add_argument("--source", type=Path, default=SOURCE)
    parser.add_argument("--include-rejected", action="store_true")
    args = parser.parse_args()

    pcs_core_root = args.pcs_core_dir.resolve().parent.parent
    if not pcs_core_root.is_dir():
        print(
            f"error: pcs-core not found at {pcs_core_root}; clone pcs-core adjacent to scientific-memory",
            file=sys.stderr,
        )
        return 1

    _copy_tree(args.source.resolve(), args.pcs_core_dir.resolve())
    if args.include_rejected:
        _copy_tree(REJECTED_SOURCE.resolve(), args.pcs_core_rejected_dir.resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
