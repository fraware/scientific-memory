#!/usr/bin/env python3
"""Verify vendored labtrust-release PCS fixtures (hashes + signed bundle shape)."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURE_DIR = REPO_ROOT / "tests" / "pcs" / "fixtures" / "labtrust-release"
MANIFEST = FIXTURE_DIR / "FIXTURE_MANIFEST.json"
SIGNED = FIXTURE_DIR / "signed_science_claim_bundle.json"
SKIP_MANIFEST_FILES = frozenset({"FIXTURE_MANIFEST.json", "FIXTURE_SOURCE.md"})


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return f"sha256:{digest.hexdigest()}"


def build_manifest() -> dict:
    if not SIGNED.is_file():
        raise FileNotFoundError(f"missing signed bundle: {SIGNED}")
    bundle = json.loads(SIGNED.read_text(encoding="utf-8"))
    claim = bundle["science_claim_bundle"]["claim_artifact"]
    artifacts: dict[str, str] = {}
    for path in sorted(FIXTURE_DIR.iterdir()):
        if not path.is_file() or path.name in SKIP_MANIFEST_FILES:
            continue
        artifacts[path.name] = _sha256(path)
    return {
        "schema_version": "v0",
        "source": "provability-fabric/tests/pcs/fixtures/labtrust-release/",
        "expected_claim_id": claim["artifact_id"],
        "signed_bundle_id": bundle.get("signed_bundle_id"),
        "artifacts": artifacts,
    }


def verify_manifest(manifest: dict) -> list[str]:
    errors: list[str] = []
    expected_claim = manifest.get("expected_claim_id")
    if not SIGNED.is_file():
        errors.append(f"missing {SIGNED.name}")
        return errors
    bundle = json.loads(SIGNED.read_text(encoding="utf-8"))
    actual_claim = bundle["science_claim_bundle"]["claim_artifact"]["artifact_id"]
    if expected_claim and actual_claim != expected_claim:
        errors.append(f"claim_id mismatch: manifest={expected_claim!r} bundle={actual_claim!r}")
    recorded = manifest.get("artifacts")
    if not isinstance(recorded, dict):
        errors.append("FIXTURE_MANIFEST.json: artifacts must be an object")
        return errors
    for name, expected_digest in sorted(recorded.items()):
        path = FIXTURE_DIR / name
        if not path.is_file():
            errors.append(f"missing fixture file: {name}")
            continue
        actual_digest = _sha256(path)
        if actual_digest != expected_digest:
            errors.append(f"{name}: digest mismatch (expected {expected_digest}, got {actual_digest})")
    return errors


def main() -> int:
    write = "--write" in sys.argv
    if write:
        FIXTURE_DIR.mkdir(parents=True, exist_ok=True)
        payload = build_manifest()
        MANIFEST.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(f"manifest -> {MANIFEST} ({len(payload['artifacts'])} files)")
        return 0
    if not MANIFEST.is_file():
        print(f"error: missing {MANIFEST} (run with --write)", file=sys.stderr)
        return 1
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    errors = verify_manifest(manifest)
    if errors:
        for err in errors:
            print(f"error: {err}", file=sys.stderr)
        return 1
    print(f"OK: labtrust-release fixtures ({manifest.get('expected_claim_id')})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
