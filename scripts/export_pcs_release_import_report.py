#!/usr/bin/env python3
"""Import labtrust-release signed bundle and export report to pcs-core release fixtures."""

from __future__ import annotations

import hashlib
import json
import shutil
import sys
from datetime import UTC, datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURE_SIGNED = (
    REPO_ROOT / "tests" / "pcs" / "fixtures" / "labtrust-release" / "signed_science_claim_bundle.json"
)
PCS_CORE_RELEASE = REPO_ROOT.parent / "pcs-core" / "examples" / "labtrust-release"
CLAIM_ID = "claim-pcs-qc-release-v0.1"


def _sha256(path: Path) -> str:
    return f"sha256:{hashlib.sha256(path.read_bytes()).hexdigest()}"


def main() -> int:
    if not FIXTURE_SIGNED.is_file():
        print(f"error: missing {FIXTURE_SIGNED}", file=sys.stderr)
        return 1

    sys.path.insert(0, str(REPO_ROOT / "pipeline" / "src"))
    from sm_pipeline.pcs_import.portal_export import write_pcs_portal_export
    from sm_pipeline.pcs_import.science_claim_bundle_importer import import_signed_bundle

    result = import_signed_bundle(FIXTURE_SIGNED, repo_root=REPO_ROOT, strict=True, write=True)
    if result.claim_id != CLAIM_ID:
        print(f"error: unexpected claim_id {result.claim_id}", file=sys.stderr)
        return 1

    report_src = (
        REPO_ROOT
        / "corpus"
        / "pcs"
        / "claims"
        / result.claim_id
        / "scientific_memory_import_report.json"
    )
    if not report_src.is_file():
        print("error: import did not write scientific_memory_import_report.json", file=sys.stderr)
        return 1

    PCS_CORE_RELEASE.mkdir(parents=True, exist_ok=True)
    report_dest = PCS_CORE_RELEASE / "scientific_memory_import_report.json"
    shutil.copy2(report_src, report_dest)
    print(f"report -> {report_dest}")

    manifest_path = PCS_CORE_RELEASE / "RELEASE_FIXTURE_MANIFEST.json"
    if manifest_path.is_file():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        artifacts = manifest.get("artifacts")
        if isinstance(artifacts, dict):
            artifacts["scientific_memory_import_report.json"] = _sha256(report_dest)
            sm_commit = json.loads(report_dest.read_text(encoding="utf-8")).get(
                "scientific_memory_commit"
            )
            if isinstance(sm_commit, str) and len(sm_commit) == 40:
                manifest["scientific_memory_commit"] = sm_commit
            manifest["generated_at"] = (
                datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
            )
            manifest_path.write_text(
                json.dumps(manifest, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            print(f"manifest updated -> {manifest_path}")

    write_pcs_portal_export(REPO_ROOT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
