#!/usr/bin/env python3
"""Copy canonical PCS schemas from pcs-core into scientific-memory (consumer mirror)."""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

# Canonical v0.1 artifacts Scientific Memory imports/renders.
CANONICAL_SCHEMAS = (
    "ReleaseManifest.v0.schema.json",
    "HandoffManifest.v0.schema.json",
    "ReleaseChainValidationResult.v0.schema.json",
    "SignedScienceClaimBundle.v0.schema.json",
    "ScienceClaimBundle.v0.schema.json",
    "VerificationResult.v0.schema.json",
    "ClaimArtifact.v0.schema.json",
    "AssumptionSet.v0.schema.json",
    "RuntimeReceipt.v0.schema.json",
    "TraceCertificate.v0.schema.json",
    "EvidenceBundle.v0.schema.json",
    "SourceSpan.v0.schema.json",
    "common.defs.json",
)

LEGACY_ALIASES = {
    "signed_science_claim_bundle.schema.json": "SignedScienceClaimBundle.v0.schema.json",
    "science_claim_bundle.schema.json": "ScienceClaimBundle.v0.schema.json",
    "verification_result.schema.json": "VerificationResult.v0.schema.json",
}


def _find_pcs_core_schemas(repo_root: Path) -> Path:
    candidates = [
        repo_root / "pcs-core" / "schemas",
        repo_root.parent / "pcs-core" / "schemas",
        Path(__file__).resolve().parents[1].parent / "pcs-core" / "schemas",
    ]
    for path in candidates:
        if (path / "SignedScienceClaimBundle.v0.schema.json").is_file():
            return path
    raise FileNotFoundError(
        "pcs-core schemas not found. Clone pcs-core adjacent to scientific-memory "
        "or set PCS_CORE_SCHEMAS_DIR."
    )


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    src = Path(sys.argv[1]) if len(sys.argv) > 1 else _find_pcs_core_schemas(repo_root)
    dest = repo_root / "schemas" / "pcs"
    dest.mkdir(parents=True, exist_ok=True)
    # Never overwrite LabTrust legacy mirrors (schemas/pcs/legacy/).
    (dest / "legacy").mkdir(exist_ok=True)

    copied: list[str] = []
    for name in CANONICAL_SCHEMAS:
        source = src / name
        if not source.is_file():
            print(f"skip missing: {name}", file=sys.stderr)
            continue
        shutil.copy2(source, dest / name)
        copied.append(name)

    manifest = {
        "source": str(src.resolve()),
        "canonical_schemas": copied,
        "legacy_aliases": LEGACY_ALIASES,
        "note": "Scientific Memory mirrors pcs-core; pcs-core remains canonical.",
    }
    (dest / "SCHEMA_MIRROR.json").write_text(
        json.dumps(manifest, indent=2) + "\n",
        encoding="utf-8",
    )

    print(f"Synced {len(copied)} schemas from {src} -> {dest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
