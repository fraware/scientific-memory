#!/usr/bin/env python3
"""Regenerate strict-mode negative fixtures from labtrust-release signed bundle."""

from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
BASE = REPO_ROOT / "tests" / "pcs" / "fixtures" / "labtrust-release"
SIGNED = BASE / "signed_science_claim_bundle.json"


def main() -> int:
    src = json.loads(SIGNED.read_text(encoding="utf-8"))
    for name, field in (
        ("missing_claim_signature.json", "signature_or_digest"),
        ("missing_claim_source_commit.json", "source_commit"),
    ):
        copy = json.loads(json.dumps(src))
        copy["science_claim_bundle"]["claim_artifact"].pop(field, None)
        (BASE / name).write_text(json.dumps(copy, indent=2) + "\n", encoding="utf-8")
        print(f"wrote {name}")

    placeholder = json.loads(json.dumps(src))
    placeholder_commit = "cccccccccccccccccccccccccccccccccccccccc"
    placeholder["verification_result"]["source_commit"] = placeholder_commit
    placeholder["source_commit"] = placeholder_commit
    (BASE / "invalid_placeholder_pf_source_commit.json").write_text(
        json.dumps(placeholder, indent=2) + "\n", encoding="utf-8"
    )
    print("wrote invalid_placeholder_pf_source_commit.json")

    local_dev = json.loads(json.dumps(src))
    local_dev["science_claim_bundle"]["local_dev"] = True
    (BASE / "invalid_local_dev_release.json").write_text(
        json.dumps(local_dev, indent=2) + "\n", encoding="utf-8"
    )
    print("wrote invalid_local_dev_release.json")
    import subprocess
    import sys

    manifest = REPO_ROOT / "scripts" / "verify_labtrust_release_fixture.py"
    subprocess.run([sys.executable, str(manifest), "--write"], check=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
