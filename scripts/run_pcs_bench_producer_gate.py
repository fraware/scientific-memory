#!/usr/bin/env python3
"""Release-grade Scientific Memory PCS benchmark producer gate (cross-platform)."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PIPELINE_SRC = REPO_ROOT / "pipeline" / "src"
sys.path.insert(0, str(PIPELINE_SRC))


def _python() -> str:
    for candidate in (
        REPO_ROOT / ".venv" / "Scripts" / "python.exe",
        REPO_ROOT / ".venv" / "bin" / "python",
    ):
        if candidate.is_file():
            return str(candidate)
    return sys.executable


def _resolve_pcs_core(explicit: str | None) -> Path:
    from sm_pipeline.benchmark.pcs_core_benchmark_validate import (
        resolve_pcs_core_from_env,
        resolve_pcs_core_root,
    )

    if explicit:
        root = resolve_pcs_core_root(explicit, repo_root=REPO_ROOT)
        if root is not None:
            return root
    env_root = resolve_pcs_core_from_env(repo_root=REPO_ROOT)
    if env_root is not None:
        return env_root
    for candidate in (REPO_ROOT / "pcs-core", REPO_ROOT.parent / "pcs-core"):
        if (candidate / "schemas").is_dir():
            return candidate.resolve()
    print(
        "error: pcs-core checkout required (set PCS_CORE_PATH or clone sibling pcs-core)",
        file=sys.stderr,
    )
    raise SystemExit(1)


def _run(cmd: list[str], *, env: dict[str, str] | None = None) -> None:
    merged = os.environ.copy()
    merged["PYTHONPATH"] = str(PIPELINE_SRC) + (
        os.pathsep + merged["PYTHONPATH"] if merged.get("PYTHONPATH") else ""
    )
    if env:
        merged.update(env)
    if cmd and cmd[0] == sys.executable:
        cmd = [_python(), *cmd[1:]]
    print("==>", " ".join(cmd))
    subprocess.run(cmd, cwd=REPO_ROOT, env=merged, check=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--cases",
        default=os.environ.get("PCS_BENCH_CASES", "benchmarks/rendering/labtrust_qc_release"),
        help="Benchmark cases directory (relative to repo root)",
    )
    parser.add_argument(
        "--out",
        default=os.environ.get("PCS_BENCH_OUT", "benchmark_runs/labtrust_rendering"),
        help="Benchmark output directory (relative to repo root)",
    )
    parser.add_argument(
        "--pcs-core",
        default=os.environ.get("PCS_CORE_PATH", ""),
        help="pcs-core checkout root",
    )
    parser.add_argument(
        "--skip-pcs-bench-cli",
        action="store_true",
        help="Do not invoke external pcs-bench validate-ingest",
    )
    parser.add_argument(
        "--require-pcs-bench-cli",
        action="store_true",
        help="Fail when pcs-bench is not on PATH (recommended for release trains)",
    )
    parser.add_argument(
        "--release-grade",
        action="store_true",
        default=True,
        help="Pass --release-grade to pcs-bench validate-ingest (default: on)",
    )
    parser.add_argument(
        "--no-release-grade",
        action="store_false",
        dest="release_grade",
        help="Omit --release-grade from pcs-bench validate-ingest",
    )
    args = parser.parse_args()

    pcs_core = _resolve_pcs_core(args.pcs_core.strip() or None)
    cases = Path(args.cases)
    out = Path(args.out)
    if not cases.is_absolute():
        cases = (REPO_ROOT / cases).resolve()
    else:
        cases = cases.resolve()
    if not out.is_absolute():
        out = (REPO_ROOT / out).resolve()
    else:
        out = out.resolve()
    ingest = out / "pcs_bench_ingest.v0.json"

    def _repo_rel(path: Path) -> str:
        try:
            return str(path.relative_to(REPO_ROOT))
        except ValueError:
            return str(path)

    _run(
        [
            sys.executable,
            "-m",
            "sm_pipeline.cli",
            "pcs-benchmark-rendering",
            "--cases",
            _repo_rel(cases),
            "--out",
            _repo_rel(out),
            "--validate-pcs-core-output",
            str(pcs_core),
            "--release-grade",
        ],
    )

    validate_cmd = [
        sys.executable,
        str(REPO_ROOT / "scripts/validate_pcs_bench_ingest.py"),
        "--input",
        _repo_rel(ingest),
        "--pcs-core",
        str(pcs_core),
        "--release-grade",
        "--skip-pcs-bench-cli",
    ]
    _run(validate_cmd)

    if not args.skip_pcs_bench_cli:
        pcs_bench = os.environ.get("PCS_BENCH_CLI", "pcs-bench")
        if shutil.which(pcs_bench):
            pcs_cmd = [
                pcs_bench,
                "validate-ingest",
                "--input",
                str(ingest),
                "--pcs-core",
                str(pcs_core),
            ]
            if args.release_grade:
                pcs_cmd.append("--release-grade")
            _run(pcs_cmd)
        elif args.require_pcs_bench_cli:
            print(f"error: {pcs_bench} not on PATH; install pcs-bench for release-grade gate", file=sys.stderr)
            return 1
        else:
            print(f"warn: {pcs_bench} not on PATH; skipped external validate-ingest", file=sys.stderr)

    try:
        from sm_pipeline.benchmark.bench_registry import refresh_registry_source_commit

        commit = refresh_registry_source_commit(REPO_ROOT)
        print(f"Updated suite_registry.v0.json source_commit -> {commit}")
    except (OSError, ValueError) as exc:
        print(f"warn: could not refresh suite registry source_commit: {exc}", file=sys.stderr)

    print(f"OK: PCS benchmark producer gate passed -> {ingest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
