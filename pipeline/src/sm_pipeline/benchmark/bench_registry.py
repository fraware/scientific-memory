"""PCS-bench suite registry for Scientific Memory rendering benchmarks."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

from sm_pipeline.benchmark.pcs_core_coverage import SOURCE_REPO
from sm_pipeline.pcs_validate.canonical_hash import canonical_hash

REGISTRY_REL = Path("benchmarks/pcs_bench/suite_registry.v0.json")


def load_suite_registry(repo_root: Path) -> dict[str, Any]:
    path = (repo_root / REGISTRY_REL).resolve()
    if not path.is_file():
        raise FileNotFoundError(f"missing suite registry: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"expected object in {path}")
    return data


def suite_entry(registry: dict[str, Any], suite_id: str) -> dict[str, Any] | None:
    for row in registry.get("suites") or []:
        if isinstance(row, dict) and row.get("suite_id") == suite_id:
            return row
    return None


def validate_suite_id(repo_root: Path, suite_id: str) -> str | None:
    registry = load_suite_registry(repo_root)
    if suite_entry(registry, suite_id) is None:
        known = [
            str(row.get("suite_id"))
            for row in (registry.get("suites") or [])
            if isinstance(row, dict) and row.get("suite_id")
        ]
        return f"unknown suite_id {suite_id!r}; known: {', '.join(known)}"
    return None


def _resolve_source_commit(repo_root: Path) -> str:
    try:
        proc = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=True,
            timeout=10,
        )
        return proc.stdout.strip() or "unknown"
    except (OSError, subprocess.SubprocessError):
        return "unknown"


def refresh_registry_source_commit(repo_root: Path) -> str:
    """Stamp suite_registry.v0.json source_commit from git HEAD (producer provenance)."""
    path = (repo_root / REGISTRY_REL).resolve()
    registry = load_suite_registry(repo_root)
    commit = _resolve_source_commit(repo_root)
    registry["source_commit"] = commit
    path.write_text(json.dumps(registry, indent=2) + "\n", encoding="utf-8")
    return commit


def build_run_suite_manifest(
    *,
    suite_id: str,
    out_dir: Path,
    ingest_path: Path,
    passed: bool,
) -> dict[str, Any]:
    """Per-run pointer from benchmark output dir back to registry suite."""
    manifest = {
        "schema_version": "v0",
        "suite_id": suite_id,
        "registry_path": str(REGISTRY_REL).replace("\\", "/"),
        "ingest_path": str(ingest_path.resolve()),
        "output_dir": str(out_dir.resolve()),
        "passed": passed,
        "source_repo": SOURCE_REPO,
    }
    manifest["signature_or_digest"] = canonical_hash(manifest)
    return manifest
