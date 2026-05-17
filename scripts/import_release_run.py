#!/usr/bin/env python3
"""Import signed bundle from release-run/, write SM report, validate, promote atomically."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RUN = REPO_ROOT / "release-run"
SIGNED = "signed_science_claim_bundle.json"
REPORT = "scientific_memory_import_report.json"
MANIFEST = "RELEASE_FIXTURE_MANIFEST.json"
CLAIM_ID = "claim-pcs-qc-release-v0.1"
SM_SOURCE_REPO = "https://github.com/fraware/scientific-memory"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path, default=DEFAULT_RUN)
    parser.add_argument("--promote", action="store_true", help="Promote to fixtures after import")
    parser.add_argument("--pcs-core", action="store_true", help="Also promote to pcs-core/examples")
    args = parser.parse_args()

    run_dir = args.run_dir.resolve()
    signed_path = run_dir / SIGNED
    if not signed_path.is_file():
        print(f"error: missing {signed_path}", file=sys.stderr)
        return 1

    sys.path.insert(0, str(REPO_ROOT / "pipeline" / "src"))
    from sm_pipeline.pcs_import.portal_export import write_pcs_portal_export
    from sm_pipeline.pcs_import.provenance import git_head_commit
    from sm_pipeline.pcs_import.science_claim_bundle_importer import import_signed_bundle
    from sm_pipeline.pcs_validate.release_chain import validate_release_chain

    issues = validate_release_chain(run_dir)
    if issues:
        for issue in issues:
            print(f"error: {issue.format()}", file=sys.stderr)
        return 1

    result = import_signed_bundle(signed_path, repo_root=REPO_ROOT, strict=True, write=True)
    if result.claim_id != CLAIM_ID:
        print(f"error: unexpected claim_id {result.claim_id}", file=sys.stderr)
        return 1

    report_src = (
        REPO_ROOT
        / "corpus"
        / "pcs"
        / "claims"
        / result.claim_id
        / REPORT
    )
    report = json.loads(report_src.read_text(encoding="utf-8-sig"))
    sm_commit = git_head_commit(REPO_ROOT) or report.get("scientific_memory_commit")
    if sm_commit:
        report["scientific_memory_commit"] = sm_commit
    report["source_commit"] = sm_commit
    report["source_repo"] = SM_SOURCE_REPO
    report["source_bundle_path"] = SIGNED
    report["strict"] = True
    report["allow_legacy"] = False
    report["bundle_shape"] = "pcs_core"
    if report.get("verification_status") != "passed":
        print("error: import did not produce verification_status=passed", file=sys.stderr)
        return 1

    dest = run_dir / REPORT
    dest.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"report -> {dest}")

    manifest_path = run_dir / MANIFEST
    if manifest_path.is_file() and sm_commit:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
        manifest["scientific_memory_commit"] = sm_commit
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    write_pcs_portal_export(REPO_ROOT)

    if args.promote:
        import subprocess

        cmd = [
            sys.executable,
            str(REPO_ROOT / "scripts" / "promote_release_run.py"),
            "--run-dir",
            str(run_dir),
            "--refresh-hashes",
        ]
        if args.pcs_core:
            cmd.append("--pcs-core")
        subprocess.run(cmd, check=True)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
