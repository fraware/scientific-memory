#!/usr/bin/env python3
"""Optional post-eval Lean sanity check (full repo ``lake build``).

Set environment variable ``LLM_EVAL_RUN_LAKE_BUILD=1`` to run. Intended for manual or scheduled
runs after reviewing LLM suggestions — not for default PR CI (see ``runtime_budget_seconds_per_task``).

Usage (repo root)::

    LLM_EVAL_RUN_LAKE_BUILD=1 uv run python scripts/llm_eval_lean_build_optional.py
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def main() -> int:
    if os.environ.get("LLM_EVAL_RUN_LAKE_BUILD", "").strip() not in ("1", "true", "yes"):
        print(
            "Skipping: set LLM_EVAL_RUN_LAKE_BUILD=1 to run lake build.",
            file=sys.stderr,
        )
        return 0
    root = Path(__file__).resolve().parents[1]
    print(f"Running lake build in {root} ...", file=sys.stderr)
    r = subprocess.run(["lake", "build"], cwd=root, check=False)
    return int(r.returncode)


if __name__ == "__main__":
    raise SystemExit(main())
