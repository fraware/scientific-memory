"""Optional pcs-bench CLI integration for ingest validation."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


def pcs_bench_available() -> bool:
    return shutil.which("pcs-bench") is not None


def require_pcs_bench_cli() -> str | None:
    """Return an error message when pcs-bench is required but missing."""
    if pcs_bench_available():
        return None
    return "pcs-bench CLI not on PATH; install from https://github.com/fraware/pcs-bench"


def run_pcs_bench_validate_ingest(
    ingest_path: Path,
    pcs_core_root: Path,
    *,
    release_grade: bool = False,
) -> list[str]:
    """Run external pcs-bench validate-ingest when the CLI is on PATH."""
    pcs_bench = shutil.which("pcs-bench")
    if not pcs_bench:
        return []
    cmd = [
        pcs_bench,
        "validate-ingest",
        "--input",
        str(ingest_path.resolve()),
        "--pcs-core",
        str(pcs_core_root.resolve()),
    ]
    if release_grade:
        cmd.append("--release-grade")
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if proc.returncode == 0:
        return []
    lines = [line.strip() for line in (proc.stderr or proc.stdout or "").splitlines() if line.strip()]
    if not lines:
        return [f"pcs-bench validate-ingest failed (exit {proc.returncode})"]
    return [f"pcs-bench: {line}" for line in lines if not line.startswith("==")]
