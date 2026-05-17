#!/usr/bin/env python3
"""Verify vendored labtrust-release PCS fixtures (hashes, PF provenance, release manifest)."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "pipeline" / "src"))

from sm_pipeline.pcs_validate.placeholder_commits import (  # noqa: E402
    is_placeholder_commit,
    validate_source_commit_for_release,
)

FIXTURE_DIR = REPO_ROOT / "tests" / "pcs" / "fixtures" / "labtrust-release"
SIGNED = FIXTURE_DIR / "signed_science_claim_bundle.json"
RELEASE_MANIFEST = FIXTURE_DIR / "RELEASE_FIXTURE_MANIFEST.json"
SM_MANIFEST = FIXTURE_DIR / "FIXTURE_MANIFEST.json"
SKIP_SM_MANIFEST = frozenset(
    {
        "FIXTURE_MANIFEST.json",
        "FIXTURE_SOURCE.md",
        "RELEASE_FIXTURE_MANIFEST.json",
    }
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return f"sha256:{digest.hexdigest()}"


def _verify_pf_provenance(bundle: dict, pf_commit: str) -> list[str]:
    errors: list[str] = []
    vr = bundle.get("verification_result")
    if not isinstance(vr, dict):
        errors.append("signed bundle missing verification_result")
        return errors
    for label, artifact in (("verification_result", vr), ("signed_bundle", bundle)):
        commit = str(artifact.get("source_commit") or "")
        if commit != pf_commit:
            errors.append(
                f"{label}.source_commit must match manifest.provability_fabric_commit "
                f"(expected {pf_commit}, got {commit})"
            )
        msg = validate_source_commit_for_release(
            commit, path=label, local_dev=artifact.get("local_dev")
        )
        if msg:
            errors.append(msg)
    return errors


def _verify_release_manifest(manifest: dict) -> list[str]:
    errors: list[str] = []
    pf_commit = str(manifest.get("provability_fabric_commit") or "")
    if len(pf_commit) != 40 or is_placeholder_commit(pf_commit):
        errors.append("RELEASE_FIXTURE_MANIFEST: invalid provability_fabric_commit")
    for key in (
        "pcs_core_commit",
        "labtrust_gym_commit",
        "certifyedge_commit",
        "scientific_memory_commit",
    ):
        commit = str(manifest.get(key) or "")
        if len(commit) != 40 or is_placeholder_commit(commit):
            errors.append(f"RELEASE_FIXTURE_MANIFEST: invalid {key}")

    if not SIGNED.is_file():
        errors.append(f"missing {SIGNED.name}")
        return errors
    bundle = json.loads(SIGNED.read_text(encoding="utf-8"))
    errors.extend(_verify_pf_provenance(bundle, pf_commit))

    artifacts = manifest.get("artifacts")
    if not isinstance(artifacts, dict):
        errors.append("RELEASE_FIXTURE_MANIFEST: artifacts must be an object")
        return errors
    for name, expected in artifacts.items():
        path = FIXTURE_DIR / name
        if not path.is_file():
            errors.append(f"missing release artifact: {name}")
            continue
        actual = _sha256(path)
        if actual != expected:
            errors.append(f"{name}: release manifest digest mismatch")
    return errors


def build_sm_manifest() -> dict:
    bundle = json.loads(SIGNED.read_text(encoding="utf-8"))
    claim_id = bundle["science_claim_bundle"]["claim_artifact"]["artifact_id"]
    artifacts = {
        path.name: _sha256(path)
        for path in sorted(FIXTURE_DIR.iterdir())
        if path.is_file() and path.name not in SKIP_SM_MANIFEST
    }
    payload: dict = {
        "schema_version": "v0",
        "source": "pcs-core/examples/labtrust-release/",
        "expected_claim_id": claim_id,
        "signed_bundle_id": bundle.get("signed_bundle_id"),
        "artifacts": artifacts,
    }
    if RELEASE_MANIFEST.is_file():
        release = json.loads(RELEASE_MANIFEST.read_text(encoding="utf-8"))
        payload["provability_fabric_commit"] = release.get("provability_fabric_commit")
    return payload


def verify_sm_manifest(manifest: dict) -> list[str]:
    errors: list[str] = []
    recorded = manifest.get("artifacts")
    if not isinstance(recorded, dict):
        return ["FIXTURE_MANIFEST.json: artifacts must be an object"]
    for name, expected in sorted(recorded.items()):
        path = FIXTURE_DIR / name
        if not path.is_file():
            errors.append(f"missing fixture file: {name}")
            continue
        if _sha256(path) != expected:
            errors.append(f"{name}: SM fixture digest mismatch")
    return errors


def main() -> int:
    write = "--write" in sys.argv
    if write:
        payload = build_sm_manifest()
        SM_MANIFEST.write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        print(f"manifest -> {SM_MANIFEST}")
        return 0

    errors: list[str] = []
    if RELEASE_MANIFEST.is_file():
        release = json.loads(RELEASE_MANIFEST.read_text(encoding="utf-8-sig"))
        errors.extend(_verify_release_manifest(release))
    else:
        errors.append("missing RELEASE_FIXTURE_MANIFEST.json")

    if SM_MANIFEST.is_file():
        errors.extend(
            verify_sm_manifest(json.loads(SM_MANIFEST.read_text(encoding="utf-8-sig")))
        )
    else:
        errors.append("missing FIXTURE_MANIFEST.json (run with --write)")

    if errors:
        for err in errors:
            print(f"error: {err}", file=sys.stderr)
        return 1
    claim = json.loads(SIGNED.read_text(encoding="utf-8"))["science_claim_bundle"]["claim_artifact"][
        "artifact_id"
    ]
    print(f"OK: labtrust-release fixtures ({claim})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
