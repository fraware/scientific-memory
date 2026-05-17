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
DEFAULT_SIGNED = FIXTURES / "signed_science_claim_bundle.json"
DEFAULT_READ_MODEL = FIXTURES / "canonical_pcs_read_model.json"
PROVENANCE = FIXTURES / "canonical_fixture_provenance.json"
PCS_CORE_EXAMPLE = (
    REPO_ROOT / "pcs-core" / "examples" / "signed_science_claim_bundle.valid.json"
)


def _resolve_signed_source(explicit: Path | None) -> Path:
    if explicit is not None:
        return explicit.resolve()
    if DEFAULT_SIGNED.is_file():
        return DEFAULT_SIGNED
    if PCS_CORE_EXAMPLE.is_file():
        return PCS_CORE_EXAMPLE
    sibling = REPO_ROOT.parent / "pcs-core" / "examples" / "signed_science_claim_bundle.valid.json"
    if sibling.is_file():
        return sibling
    raise FileNotFoundError(
        "No signed bundle source. Pass --signed or clone pcs-core (examples/signed_science_claim_bundle.valid.json)."
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
        help="Copy --signed (or pcs-core example) into tests/pcs/fixtures/signed_science_claim_bundle.json",
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
        payload = source.read_text(encoding="utf-8")
        DEFAULT_SIGNED.write_text(payload, encoding="utf-8")
        print(f"fixture -> {DEFAULT_SIGNED}")

    bundle = json.loads(DEFAULT_SIGNED.read_text(encoding="utf-8"))
    read_model = normalize_signed_bundle(bundle)
    DEFAULT_READ_MODEL.write_text(
        json.dumps(read_model, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"read_model -> {DEFAULT_READ_MODEL} (claim_id={read_model['claim_id']})")

    if args.sync_pcs_core_alias:
        alias = FIXTURES / "valid_signed_pcs_core_bundle.json"
        alias.write_text(DEFAULT_SIGNED.read_text(encoding="utf-8"), encoding="utf-8")
        print(f"alias -> {alias}")

    from sm_pipeline.pcs_validate.bundle_detection import detect_bundle_shape

    PROVENANCE.write_text(
        json.dumps(
            {
                "fixture": DEFAULT_SIGNED.name,
                "source_path": str(source.resolve()),
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
