"""Operational lineage and registry admission helpers."""

from __future__ import annotations

import json
from pathlib import Path

from sm_pipeline.pcs_import.lineage_ops import build_operational_lineage_view
from sm_pipeline.pcs_import.registry_admission import (
    ADMISSION_FAILED,
    ADMISSION_PASSED,
    compute_registry_admission_status,
    enrich_registry_row,
)


def test_registry_admission_passed_and_failed() -> None:
    passed = compute_registry_admission_status(
        {"artifact_type": "SignedScienceClaimBundle.v0", "registry_admission_result": "admitted"},
    )
    assert passed == ADMISSION_PASSED

    failed = compute_registry_admission_status(
        {
            "artifact_type": "SignedScienceClaimBundle.v0",
            "registry_admission_result": "incomplete",
            "required_release_fields_missing": ["sha256"],
        },
    )
    assert failed == ADMISSION_FAILED

    row = enrich_registry_row(
        {
            "artifact_type": "RuntimeReceipt.v0",
            "registry_admission_result": "admitted",
            "runtime_producer": "LabTrust-Gym",
        },
    )
    assert row["admission_status"] == ADMISSION_PASSED
    assert row["allowed_runtime_producers"] == ["LabTrust-Gym"]


def _write_claim_index(root: Path, entries: list[dict]) -> None:
    pcs_dir = root / "corpus" / "pcs"
    pcs_dir.mkdir(parents=True, exist_ok=True)
    index = {
        "schema_version": "PcsClaimsIndex.v0",
        "claim_count": len(entries),
        "claims": entries,
    }
    (pcs_dir / "claims_index.json").write_text(
        json.dumps(index, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def test_operational_lineage_marks_superseded_when_newer_release_exists(tmp_path: Path) -> None:
    root = tmp_path
    cert = "cert-trace-shared"
    claim_current = "claim-release-new"
    claim_previous = "claim-release-old"
    for claim_id, release_id, imported_at, artifact_hash in (
        (claim_previous, "release-old", "2026-01-01T00:00:00Z", "sha256:" + "1" * 64),
        (claim_current, "release-new", "2026-02-01T00:00:00Z", "sha256:" + "2" * 64),
    ):
        claim_dir = root / "corpus" / "pcs" / "claims" / claim_id
        claim_dir.mkdir(parents=True)
        lineage = {
            "claim_id": claim_id,
            "certificate_id": cert,
            "release_id": release_id,
            "signed_bundle_hash": artifact_hash,
            "stale": False,
            "stale_reasons": [],
            "artifact_hashes": {
                "signed_science_claim_bundle.json": artifact_hash,
            },
        }
        (claim_dir / "lineage.json").write_text(
            json.dumps(lineage, indent=2) + "\n",
            encoding="utf-8",
        )

    _write_claim_index(
        root,
        [
            {
                "claim_id": claim_previous,
                "claim_dir": claim_previous,
                "certificate_id": cert,
                "release_id": "release-old",
                "imported_at": "2026-01-01T00:00:00Z",
            },
            {
                "claim_id": claim_current,
                "claim_dir": claim_current,
                "certificate_id": cert,
                "release_id": "release-new",
                "imported_at": "2026-02-01T00:00:00Z",
            },
        ],
    )

    older_lineage = json.loads(
        (root / "corpus" / "pcs" / "claims" / claim_previous / "lineage.json").read_text(),
    )
    view = build_operational_lineage_view(
        older_lineage,
        repo_root=root,
        claim_id=claim_previous,
        release_manifest={"release_status": "Validated"},
        validation={"status": "ProofChecked"},
    )
    assert view["claim_state"] == "superseded"
    assert not view.get("previous_release_id")
    assert "release-new" in view["newer_release_ids"]
    assert view["recommended_action"]


def test_operational_lineage_diffs_artifact_hashes_against_previous_release(
    tmp_path: Path,
) -> None:
    root = tmp_path
    cert = "cert-trace-diff"
    claim_current = "claim-current"
    claim_previous = "claim-previous"
    for claim_id, release_id, imported_at, bundle_hash, receipt_hash in (
        (
            claim_previous,
            "release-prev",
            "2026-01-01T00:00:00Z",
            "sha256:" + "a" * 64,
            "sha256:" + "b" * 64,
        ),
        (
            claim_current,
            "release-curr",
            "2026-02-01T00:00:00Z",
            "sha256:" + "c" * 64,
            "sha256:" + "b" * 64,
        ),
    ):
        claim_dir = root / "corpus" / "pcs" / "claims" / claim_id
        claim_dir.mkdir(parents=True)
        lineage = {
            "claim_id": claim_id,
            "certificate_id": cert,
            "release_id": release_id,
            "signed_bundle_hash": bundle_hash,
            "stale": False,
            "stale_reasons": [],
            "artifact_hashes": {
                "signed_science_claim_bundle.json": bundle_hash,
                "runtime_receipt.json": receipt_hash,
            },
        }
        (claim_dir / "lineage.json").write_text(
            json.dumps(lineage, indent=2) + "\n",
            encoding="utf-8",
        )

    _write_claim_index(
        root,
        [
            {
                "claim_id": claim_previous,
                "claim_dir": claim_previous,
                "certificate_id": cert,
                "release_id": "release-prev",
                "imported_at": "2026-01-01T00:00:00Z",
            },
            {
                "claim_id": claim_current,
                "claim_dir": claim_current,
                "certificate_id": cert,
                "release_id": "release-curr",
                "imported_at": "2026-02-01T00:00:00Z",
            },
        ],
    )

    current_lineage = json.loads(
        (root / "corpus" / "pcs" / "claims" / claim_current / "lineage.json").read_text(),
    )
    view = build_operational_lineage_view(
        current_lineage,
        repo_root=root,
        claim_id=claim_current,
        release_manifest={"release_status": "Validated"},
        validation={"status": "ProofChecked"},
    )
    assert view["previous_release_id"] == "release-prev"
    assert "signed_science_claim_bundle.json" in view["changed_artifacts"]
    assert "runtime_receipt.json" not in view["changed_artifacts"]
    assert view["changed_hashes"]
