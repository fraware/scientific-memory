#!/usr/bin/env python3
"""Mirror pcs-core benchmark JSON schemas into scientific-memory/schemas/pcs/benchmark."""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

BENCHMARK_SCHEMAS = (
    "BenchmarkRun.v0.schema.json",  # pcs-core per-case run (ingest embedded)
    "CoverageReport.v0.schema.json",
    "FailureLocalizationResult.v0.schema.json",
    "ProfileCoverageReport.v0.schema.json",
    "RenderingCoverageReport.v0.schema.json",
    "QueryCoverageReport.v0.schema.json",
    "FailedReleaseRenderingReport.v0.schema.json",
    "ExplainQualityReport.v0.schema.json",
    "PcsBenchIngest.v0.schema.json",
    "BenchmarkArtifactRef.v0.schema.json",
)


def _find_pcs_core_schemas(repo_root: Path) -> Path:
    candidates = [
        repo_root / "pcs-core" / "schemas",
        repo_root.parent / "pcs-core" / "schemas",
        repo_root / "pcs-core" / "schemas" / "benchmark",
        repo_root.parent / "pcs-core" / "schemas" / "benchmark",
    ]
    for path in candidates:
        if (path / "BenchmarkRun.v0.schema.json").is_file():
            return path
        bench = path / "benchmark"
        if (bench / "BenchmarkRun.v0.schema.json").is_file():
            return bench
    raise FileNotFoundError(
        "pcs-core benchmark schemas not found; clone pcs-core adjacent to scientific-memory",
    )


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    src = Path(sys.argv[1]) if len(sys.argv) > 1 else _find_pcs_core_schemas(repo_root)
    dest = repo_root / "schemas" / "pcs" / "benchmark"
    dest.mkdir(parents=True, exist_ok=True)

    copied: list[str] = []
    for name in BENCHMARK_SCHEMAS:
        source = src / name
        if not source.is_file():
            print(f"skip missing: {name}", file=sys.stderr)
            continue
        shutil.copy2(source, dest / name)
        copied.append(name)

    manifest = {
        "source": str(src.resolve()),
        "benchmark_schemas": copied,
        "note": "SM mirrors pcs-core benchmark schemas; extend SM-only fields via additionalProperties.",
    }
    (dest / "SCHEMA_SYNC.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"OK: synced {len(copied)} benchmark schemas -> {dest}")
    return 0 if copied else 1


if __name__ == "__main__":
    raise SystemExit(main())
