#!/usr/bin/env python3
"""Cross-platform PCS release fixture refresh (same steps as `just refresh-pcs-release`)."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def _python() -> str:
    for candidate in (
        REPO_ROOT / ".venv" / "Scripts" / "python.exe",
        REPO_ROOT / ".venv" / "bin" / "python",
    ):
        if candidate.is_file():
            return str(candidate)
    return sys.executable


def _run(script: str, *args: str) -> None:
    cmd = [_python(), str(REPO_ROOT / "scripts" / script), *args]
    print("==>", " ".join(cmd))
    subprocess.run(cmd, cwd=REPO_ROOT, check=True)


def main() -> int:
    steps = [
        ("sync_pcs_schemas.py", ()),
        ("sync_labtrust_release_from_pcs_core.py", ()),
        ("sync_tool_use_release_from_pcs_core.py", ("--ensure",)),
        ("sync_computation_release_from_pcs_core.py", ("--bootstrap-if-missing",)),
        ("ensure_labtrust_phase2_fixtures.py", ()),
        ("ensure_labtrust_phase2_fixtures.py", ("--release-dir", "release-run")),
        ("regenerate_labtrust_negative_fixtures.py", ()),
        ("verify_labtrust_release_fixture.py", ("--write",)),
        (
            "refresh_pcs_canonical_fixture.py",
            ("--copy-to-fixture", "--sync-pcs-core-alias"),
        ),
        ("bootstrap_pcs_rendering_benchmarks.py", ()),
    ]
    for script, args in steps:
        _run(script, *args)
    print("OK: PCS release fixtures refreshed (schemas, releases, benchmarks)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
