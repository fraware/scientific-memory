#!/usr/bin/env python3
"""Refresh PCS canonical test fixture and read model from pcs-core (or a PF signed file)."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURES = REPO_ROOT / "tests" / "pcs" / "fixtures"
LABTRUST_RELEASE_FIXTURE = (
    FIXTURES / "labtrust-release" / "signed_science_claim_bundle.json"
)
PF_SIGNED_FIXTURE = FIXTURES / "signed_science_claim_bundle.valid.json"
LEGACY_ALIAS = FIXTURES / "signed_science_claim_bundle.json"
DEFAULT_READ_MODEL = FIXTURES / "canonical_pcs_read_model.json"
PROVENANCE = FIXTURES / "canonical_fixture_provenance.json"
PF_LABTRUST_RELEASE = (
    REPO_ROOT.parent
    / "provability-fabric"
    / "tests"
    / "pcs"
    / "fixtures"
    / "labtrust-release"
    / "signed_science_claim_bundle.json"
)
LABTRUST_GYM_SIGNED = (
    REPO_ROOT.parent / "LabTrust-Gym" / "signed_science_claim_bundle.json"
)
PCS_CORE_LABTRUST_RELEASE = (
    REPO_ROOT.parent / "pcs-core" / "examples" / "labtrust-release" / "signed_science_claim_bundle.json"
)
PCS_CORE_EXAMPLE = (
    REPO_ROOT / "pcs-core" / "examples" / "signed_science_claim_bundle.valid.json"
)


def _resolve_signed_source(explicit: Path | None) -> Path:
    if explicit is not None:
        return explicit.resolve()
    if PF_LABTRUST_RELEASE.is_file():
        return PF_LABTRUST_RELEASE
    if LABTRUST_GYM_SIGNED.is_file():
        return LABTRUST_GYM_SIGNED
    if LABTRUST_RELEASE_FIXTURE.is_file():
        return LABTRUST_RELEASE_FIXTURE
    if PCS_CORE_LABTRUST_RELEASE.is_file():
        return PCS_CORE_LABTRUST_RELEASE
    if PF_SIGNED_FIXTURE.is_file():
        return PF_SIGNED_FIXTURE
    if LEGACY_ALIAS.is_file():
        return LEGACY_ALIAS
    if PCS_CORE_EXAMPLE.is_file():
        return PCS_CORE_EXAMPLE
    sibling = REPO_ROOT.parent / "pcs-core" / "examples" / "signed_science_claim_bundle.valid.json"
    if sibling.is_file():
        return sibling
    raise FileNotFoundError(
        "No signed bundle source. Pass --signed or vendor "
        "pcs-core/examples/labtrust-release/signed_science_claim_bundle.json."
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--signed",
        type=Path,
        help="PF output: signed_science_claim_bundle.json",
    )
    parser.add_argument(
        "--copy-to-fixture",
        action="store_true",
        help="Copy --signed (or pcs-core example) into tests/pcs/fixtures/signed_science_claim_bundle.valid.json",
    )
    parser.add_argument(
        "--sync-pcs-core-alias",
        action="store_true",
        help="Also write valid_signed_pcs_core_bundle.json (same bytes as canonical fixture)",
    )
    args = parser.parse_args()

    sys.path.insert(0, str(REPO_ROOT / "pipeline" / "src"))
    from sm_pipeline.pcs_import.artifact_normalizer import normalize_signed_bundle

    source = _resolve_signed_source(args.signed)
    if args.copy_to_fixture or args.signed is not None:
        FIXTURES.mkdir(parents=True, exist_ok=True)
        release_dir = FIXTURES / "labtrust-release"
        release_dir.mkdir(parents=True, exist_ok=True)
        if source.resolve() != LABTRUST_RELEASE_FIXTURE.resolve():
            if PF_LABTRUST_RELEASE.parent.is_dir():
                for path in PF_LABTRUST_RELEASE.parent.iterdir():
                    if path.is_file() and path.name != "FIXTURE_SOURCE.md":
                        shutil.copy2(path, release_dir / path.name)
            else:
                shutil.copy2(source, LABTRUST_RELEASE_FIXTURE)
        payload = LABTRUST_RELEASE_FIXTURE.read_text(encoding="utf-8")
        PF_SIGNED_FIXTURE.write_text(payload, encoding="utf-8")
        LEGACY_ALIAS.write_text(payload, encoding="utf-8")
        print(f"fixture -> {LABTRUST_RELEASE_FIXTURE}")

    bundle_path = (
        LABTRUST_RELEASE_FIXTURE if LABTRUST_RELEASE_FIXTURE.is_file() else PF_SIGNED_FIXTURE
    )
    bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
    read_model = normalize_signed_bundle(bundle)
    DEFAULT_READ_MODEL.write_text(
        json.dumps(read_model, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"read_model -> {DEFAULT_READ_MODEL} (claim_id={read_model['claim_id']})")

    if args.sync_pcs_core_alias:
        alias = FIXTURES / "valid_signed_pcs_core_bundle.json"
        alias.write_text(PF_SIGNED_FIXTURE.read_text(encoding="utf-8"), encoding="utf-8")
        print(f"alias -> {alias}")

    from sm_pipeline.pcs_validate.bundle_detection import detect_bundle_shape

    import hashlib

    signed_bytes = bundle_path.read_bytes()
    signed_sha256 = f"sha256:{hashlib.sha256(signed_bytes).hexdigest()}"

    PROVENANCE.write_text(
        json.dumps(
            {
                "fixture": "labtrust-release/signed_science_claim_bundle.json",
                "source": "provability-fabric/tests/pcs/fixtures/labtrust-release/",
                "source_path": (
                    "tests/pcs/fixtures/labtrust-release/signed_science_claim_bundle.json"
                    if source.resolve() == LABTRUST_RELEASE_FIXTURE.resolve()
                    else str(source.resolve())
                ),
                "signed_bundle_sha256": signed_sha256,
                "bundle_shape": detect_bundle_shape(bundle),
                "claim_id": read_model["claim_id"],
                "refresh_command": "just refresh-pcs-fixtures",
                "pf_sign_command": (
                    "pf sign science-claim science_claim_bundle.certified.json "
                    "--out signed_science_claim_bundle.json"
                ),
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"provenance -> {PROVENANCE}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
