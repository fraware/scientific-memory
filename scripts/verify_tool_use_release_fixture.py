#!/usr/bin/env python3
"""Verify vendored tool-use-release PCS fixtures (manifest digests, strict validation)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURE_DIR = REPO_ROOT / "tests" / "pcs" / "fixtures" / "tool-use-release"


def main() -> int:
    sys.path.insert(0, str(REPO_ROOT / "pipeline" / "src"))
    from sm_pipeline.pcs_validate.release_paths import (
        resolve_release_chain_validation_path,
        resolve_release_manifest_path,
    )
    from sm_pipeline.pcs_validate.release_chain_validation import validate_release_chain_validation
    from sm_pipeline.pcs_validate.release_manifest import validate_release_manifest

    if not FIXTURE_DIR.is_dir():
        print(f"error: missing {FIXTURE_DIR}", file=sys.stderr)
        return 1

    manifest_path = resolve_release_manifest_path(FIXTURE_DIR)
    validation_path = resolve_release_chain_validation_path(FIXTURE_DIR)
    phase2_model = FIXTURE_DIR / ".phase2-read-model.json"

    manifest_errors = validate_release_manifest(manifest_path, repo_root=REPO_ROOT)
    if manifest_errors:
        for err in manifest_errors:
            print(f"error: manifest: {err}", file=sys.stderr)
        return 1

    manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    validation_errors = validate_release_chain_validation(
        validation_path,
        repo_root=REPO_ROOT,
        expected_release_id=str(manifest.get("release_id") or ""),
    )
    if validation_errors:
        for err in validation_errors:
            print(f"error: validation: {err}", file=sys.stderr)
        return 1

    if not phase2_model.is_file():
        print(f"error: missing {phase2_model.name} (run ensure_tool_use_phase2_fixtures)", file=sys.stderr)
        return 1

    print(f"OK: tool-use-release fixtures ({manifest.get('release_id')})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
