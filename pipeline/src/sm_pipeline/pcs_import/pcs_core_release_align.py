"""Align SM release fixtures with pcs-core published labtrust-release manifest."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

PCS_LABTRUST_MANIFEST_NAMES = (
    "release_manifest.v0.json",
    "ReleaseManifest.v0.json",
)


def resolve_pcs_core_labtrust_release_dir(repo_root: Path) -> Path | None:
    import os

    env = os.environ.get("PCS_CORE_PATH", "").strip()
    candidates: list[Path] = []
    if env:
        candidates.append(Path(env) / "examples" / "labtrust-release")
    candidates.extend(
        [
            repo_root / "pcs-core" / "examples" / "labtrust-release",
            repo_root.parent / "pcs-core" / "examples" / "labtrust-release",
        ],
    )
    for path in candidates:
        if path.is_dir():
            return path
    return None


def load_pcs_core_published_release_manifest(repo_root: Path) -> dict[str, Any] | None:
    release_dir = resolve_pcs_core_labtrust_release_dir(repo_root)
    if release_dir is None:
        return None
    for name in PCS_LABTRUST_MANIFEST_NAMES:
        path = release_dir / name
        if path.is_file():
            data = json.loads(path.read_text(encoding="utf-8-sig"))
            return data if isinstance(data, dict) else None
    return None


def pcs_core_scientific_memory_commit(repo_root: Path) -> str | None:
    manifest = load_pcs_core_published_release_manifest(repo_root)
    if manifest is None:
        return None
    producer_repos = manifest.get("producer_repos")
    if not isinstance(producer_repos, dict):
        return None
    sm = producer_repos.get("scientific_memory")
    if not isinstance(sm, dict):
        return None
    commit = sm.get("commit")
    return commit if isinstance(commit, str) and commit else None


def align_scientific_memory_producer_repos(
    manifest: dict[str, Any],
    *,
    repo_root: Path,
) -> dict[str, Any]:
    commit = pcs_core_scientific_memory_commit(repo_root)
    if not commit:
        return manifest
    out = dict(manifest)
    producer_repos = dict(out.get("producer_repos") or {})
    sm = dict(producer_repos.get("scientific_memory") or {})
    sm["commit"] = commit
    if not sm.get("repo"):
        sm["repo"] = "https://github.com/fraware/scientific-memory"
    producer_repos["scientific_memory"] = sm
    out["producer_repos"] = producer_repos
    artifacts = dict(out.get("artifacts") or {})
    import_report = dict(artifacts.get("scientific_memory_import_report.json") or {})
    if import_report:
        import_report["source_commit"] = commit
        artifacts["scientific_memory_import_report.json"] = import_report
        out["artifacts"] = artifacts
    from sm_pipeline.pcs_validate.canonical_hash import canonical_hash

    out["signature_or_digest"] = canonical_hash({k: v for k, v in out.items() if k != "signature_or_digest"})
    return out


def align_legacy_fixture_scientific_memory_commit(release_dir: Path, *, repo_root: Path) -> None:
    commit = pcs_core_scientific_memory_commit(repo_root)
    if not commit:
        return
    legacy_path = release_dir / "RELEASE_FIXTURE_MANIFEST.json"
    if not legacy_path.is_file():
        return
    legacy = json.loads(legacy_path.read_text(encoding="utf-8-sig"))
    legacy["scientific_memory_commit"] = commit
    legacy_path.write_text(json.dumps(legacy, indent=2) + "\n", encoding="utf-8")
    report_path = release_dir / "scientific_memory_import_report.json"
    if report_path.is_file():
        report = json.loads(report_path.read_text(encoding="utf-8-sig"))
        report["scientific_memory_commit"] = commit
        report["source_commit"] = commit
        report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
