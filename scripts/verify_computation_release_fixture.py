#!/usr/bin/env python3
"""Verify computation-release PCS fixtures (manifest digests, strict validation, phase2 golden)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURE_DIR = REPO_ROOT / "tests" / "pcs" / "fixtures" / "computation-release"
REJECTED_DIR = REPO_ROOT / "tests" / "pcs" / "fixtures" / "computation-rejected-release"
EXPECTED_WORKFLOW_ID = "scientific_computation.reproducibility_v0"


def _verify_dir(release_dir: Path, *, label: str) -> list[str]:
    sys.path.insert(0, str(REPO_ROOT / "pipeline" / "src"))
    from sm_pipeline.pcs_validate.release_paths import (
        resolve_release_chain_validation_path,
        resolve_release_manifest_path,
    )
    from sm_pipeline.pcs_validate.release_chain_validation import validate_release_chain_validation
    from sm_pipeline.pcs_validate.release_manifest import validate_release_manifest

    errors: list[str] = []
    if not release_dir.is_dir():
        return [f"missing {release_dir}"]

    manifest_path = resolve_release_manifest_path(release_dir)
    validation_path = resolve_release_chain_validation_path(release_dir)
    phase2_model = release_dir / ".phase2-read-model.json"

    manifest_errors = validate_release_manifest(manifest_path, repo_root=REPO_ROOT)
    errors.extend(f"manifest: {err}" for err in manifest_errors)

    manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    validation_errors = validate_release_chain_validation(
        validation_path,
        repo_root=REPO_ROOT,
        expected_release_id=str(manifest.get("release_id") or ""),
    )
    errors.extend(f"validation: {err}" for err in validation_errors)

    if not phase2_model.is_file():
        errors.append(
            f"missing {phase2_model.name} (run: just bootstrap-computation-release)",
        )
    else:
        model = json.loads(phase2_model.read_text(encoding="utf-8"))
        if model.get("workflow_id") != EXPECTED_WORKFLOW_ID:
            errors.append(
                f"phase2 workflow_id expected {EXPECTED_WORKFLOW_ID!r}, got {model.get('workflow_id')!r}",
            )
        for key in (
            "dataset_receipt",
            "environment_receipt",
            "computation_run_receipt",
            "result_artifact",
            "computation_witness",
        ):
            if not model.get(key):
                errors.append(f"phase2 read model missing {key}")

    if not errors:
        print(f"OK: {label} ({manifest.get('release_id')})")
    return errors


def main() -> int:
    errors: list[str] = []
    errors.extend(_verify_dir(FIXTURE_DIR, label="computation-release"))
    errors.extend(_verify_dir(REJECTED_DIR, label="computation-rejected-release"))
    if errors:
        for err in errors:
            print(f"error: {err}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
