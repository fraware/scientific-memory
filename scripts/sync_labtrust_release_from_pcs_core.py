#!/usr/bin/env python3
"""Sync release-run and SM fixtures from canonical pcs-core/examples/labtrust-release/."""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PCS_CORE = REPO_ROOT.parent / "pcs-core" / "examples" / "labtrust-release"
DEFAULT_RUN = REPO_ROOT / "release-run"
FIXTURE_DIR = REPO_ROOT / "tests" / "pcs" / "fixtures" / "labtrust-release"
MANIFEST_ARTIFACTS = (
    "trace.json",
    "runtime_receipt.json",
    "trace_certificate.json",
    "science_claim_bundle.pending.json",
    "science_claim_bundle.certified.json",
    "verification_result.json",
    "signed_science_claim_bundle.json",
    "scientific_memory_import_report.json",
    "RELEASE_FIXTURE_MANIFEST.json",
)
CLAIM_ID = "claim-pcs-qc-release-v0.1"


def sync_from_pcs_core(
    pcs_core_dir: Path,
    *,
    run_dir: Path,
    fixture_dir: Path,
    import_corpus: bool,
) -> None:
    if not (pcs_core_dir / "signed_science_claim_bundle.json").is_file():
        print(f"error: missing canonical signed bundle at {pcs_core_dir}", file=sys.stderr)
        raise SystemExit(1)

    for name in MANIFEST_ARTIFACTS:
        src = pcs_core_dir / name
        if not src.is_file():
            print(f"error: canonical release missing {name}", file=sys.stderr)
            raise SystemExit(1)

    run_dir.mkdir(parents=True, exist_ok=True)
    fixture_dir.mkdir(parents=True, exist_ok=True)
    for name in MANIFEST_ARTIFACTS:
        shutil.copy2(pcs_core_dir / name, run_dir / name)
        shutil.copy2(pcs_core_dir / name, fixture_dir / name)

    print(f"synced {pcs_core_dir} -> {run_dir}")
    print(f"synced {pcs_core_dir} -> {fixture_dir}")

    sys.path.insert(0, str(REPO_ROOT / "pipeline" / "src"))
    from sm_pipeline.pcs_validate.release_chain import validate_release_chain

    for label, directory in (("release-run", run_dir), ("fixtures", fixture_dir)):
        issues = validate_release_chain(directory)
        if issues:
            for issue in issues:
                print(f"error: {label}: {issue.format()}", file=sys.stderr)
            raise SystemExit(1)

    if not import_corpus:
        return

    from sm_pipeline.pcs_import.portal_export import write_pcs_portal_export
    from sm_pipeline.pcs_import.science_claim_bundle_importer import import_signed_bundle

    signed_path = fixture_dir / "signed_science_claim_bundle.json"
    report_path = fixture_dir / "scientific_memory_import_report.json"
    result = import_signed_bundle(signed_path, repo_root=REPO_ROOT, strict=True, write=True)
    if result.claim_id != CLAIM_ID:
        print(f"error: unexpected claim_id {result.claim_id}", file=sys.stderr)
        raise SystemExit(1)

    claim_dir = REPO_ROOT / "corpus" / "pcs" / "claims" / result.claim_id
    shutil.copy2(report_path, claim_dir / "scientific_memory_import_report.json")
    shutil.copy2(report_path, run_dir / "scientific_memory_import_report.json")
    write_pcs_portal_export(REPO_ROOT)
    print(f"corpus import -> {claim_dir}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pcs-core-dir", type=Path, default=DEFAULT_PCS_CORE)
    parser.add_argument("--run-dir", type=Path, default=DEFAULT_RUN)
    parser.add_argument("--fixture-dir", type=Path, default=FIXTURE_DIR)
    parser.add_argument("--no-corpus", action="store_true")
    args = parser.parse_args()
    sync_from_pcs_core(
        args.pcs_core_dir.resolve(),
        run_dir=args.run_dir.resolve(),
        fixture_dir=args.fixture_dir.resolve(),
        import_corpus=not args.no_corpus,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
