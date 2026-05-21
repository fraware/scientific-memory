#!/usr/bin/env python3
"""Update benchmarks/pcs_bench/suite_registry.v0.json source_commit from git HEAD."""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "pipeline" / "src"))

from sm_pipeline.benchmark.bench_registry import refresh_registry_source_commit


def main() -> int:
    commit = refresh_registry_source_commit(REPO_ROOT)
    print(f"OK: suite_registry source_commit -> {commit}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
