#!/usr/bin/env python3
"""Sync tool-use release fixtures from pcs-core/examples/tool-use-release/."""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PCS_CORE = REPO_ROOT.parent / "pcs-core" / "examples" / "tool-use-release"
FIXTURE_DIR = REPO_ROOT / "tests" / "pcs" / "fixtures" / "tool-use-release"
EXAMPLES_DIR = REPO_ROOT / "examples" / "tool-use-release"


def sync_from_pcs_core(pcs_core_dir: Path, *, fixture_dir: Path, examples_dir: Path) -> None:
    if not (pcs_core_dir / "release_manifest.v0.json").is_file():
        print(f"error: missing tool-use release at {pcs_core_dir}", file=sys.stderr)
        raise SystemExit(1)

    for target in (fixture_dir, examples_dir):
        target.mkdir(parents=True, exist_ok=True)
        for path in sorted(pcs_core_dir.iterdir()):
            if path.is_file():
                shutil.copy2(path, target / path.name)
        print(f"synced tool-use release -> {target}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pcs-core-dir", type=Path, default=DEFAULT_PCS_CORE)
    parser.add_argument("--fixture-dir", type=Path, default=FIXTURE_DIR)
    parser.add_argument("--examples-dir", type=Path, default=EXAMPLES_DIR)
    parser.add_argument("--ensure", action="store_true", help="Run ensure_tool_use_phase2_fixtures after sync")
    args = parser.parse_args()

    sync_from_pcs_core(
        args.pcs_core_dir.resolve(),
        fixture_dir=args.fixture_dir.resolve(),
        examples_dir=args.examples_dir.resolve(),
    )

    if args.ensure:
        import subprocess

        subprocess.run(
            [sys.executable, str(REPO_ROOT / "scripts" / "ensure_tool_use_phase2_fixtures.py")],
            check=True,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
