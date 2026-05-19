"""Release comparison via lineage index."""

from __future__ import annotations

import json
from pathlib import Path

from sm_pipeline.pcs_import.release_compare import compare_releases


def _write_claim_index(root: Path, entries: list[dict]) -> None:
    pcs_dir = root / "corpus" / "pcs"
    pcs_dir.mkdir(parents=True, exist_ok=True)
    (pcs_dir / "claims_index.json").write_text(
        json.dumps(
            {
                "schema_version": "PcsClaimsIndex.v0",
                "claim_count": len(entries),
                "claims": entries,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


def test_compare_releases_reports_hash_and_commit_deltas(tmp_path: Path) -> None:
    root = tmp_path
    for claim_id, release_id, imported_at, bundle_hash, cert, commit in (
        (
            "claim-old",
            "release-old",
            "2026-01-01T00:00:00Z",
            "sha256:" + "1" * 64,
            "cert-a",
            "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        ),
        (
            "claim-new",
            "release-new",
            "2026-02-01T00:00:00Z",
            "sha256:" + "2" * 64,
            "cert-b",
            "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
        ),
    ):
        claim_dir = root / "corpus" / "pcs" / "claims" / claim_id
        claim_dir.mkdir(parents=True)
        lineage = {
            "claim_id": claim_id,
            "release_id": release_id,
            "certificate_id": cert,
            "signed_bundle_hash": bundle_hash,
            "source_commits": {"scientific_memory": commit},
            "artifact_hashes": {"signed_science_claim_bundle.json": bundle_hash},
            "stale": False,
            "stale_reasons": [],
        }
        (claim_dir / "lineage.json").write_text(
            json.dumps(lineage, indent=2) + "\n",
            encoding="utf-8",
        )

    _write_claim_index(
        root,
        [
            {
                "claim_id": "claim-old",
                "claim_dir": "claim-old",
                "release_id": "release-old",
                "imported_at": "2026-01-01T00:00:00Z",
            },
            {
                "claim_id": "claim-new",
                "claim_dir": "claim-new",
                "release_id": "release-new",
                "imported_at": "2026-02-01T00:00:00Z",
            },
        ],
    )

    result = compare_releases(root, old_release_id="release-old", new_release_id="release-new")
    assert result["old_release_id"] == "release-old"
    assert result["new_release_id"] == "release-new"
    assert "signed_science_claim_bundle.json" in result["changed_artifacts"]
    assert result["changed_source_commits"]
    assert result["changed_certificates"]
    assert result["staleness_impact"]
    assert result["recommended_action"]
    assert "changed_workflow_profile" in result
    assert "changed_registry_checks" in result
    assert "changed_formal_checks" in result


def test_compare_releases_diffs_formal_trust_lineage(tmp_path: Path) -> None:
    root = tmp_path
    for claim_id, release_id, lean_status, theorems in (
        (
            "claim-old",
            "release-old",
            "ProofChecked",
            ["PCS.CertificateMatchesRuntime"],
        ),
        (
            "claim-new",
            "release-new",
            "Failed",
            ["PCS.CertificateMatchesRuntime", "PCS.SignedBundleAdmissible"],
        ),
    ):
        claim_dir = root / "corpus" / "pcs" / "claims" / claim_id
        claim_dir.mkdir(parents=True)
        (claim_dir / "lineage.json").write_text(
            json.dumps(
                {
                    "claim_id": claim_id,
                    "release_id": release_id,
                    "signed_bundle_hash": "sha256:" + ("1" if claim_id.endswith("old") else "2") * 64,
                    "artifact_hashes": {},
                    "formal_trust": {
                        "lean_check_status": lean_status,
                        "obligation_set_id": f"obl-{claim_id}",
                        "lean_theorems": theorems,
                    },
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

    _write_claim_index(
        root,
        [
            {
                "claim_id": "claim-old",
                "claim_dir": "claim-old",
                "release_id": "release-old",
                "imported_at": "2026-01-01T00:00:00Z",
            },
            {
                "claim_id": "claim-new",
                "claim_dir": "claim-new",
                "release_id": "release-new",
                "imported_at": "2026-02-01T00:00:00Z",
            },
        ],
    )

    result = compare_releases(root, old_release_id="release-old", new_release_id="release-new")
    assert result["changed_formal_checks"]
    assert any(row["field"] == "lean_check_status" for row in result["changed_formal_checks"])
    assert "formal_checks_changed" in result["staleness_impact"]


def test_compare_releases_diffs_workflow_profile_and_registry_checks(tmp_path: Path) -> None:
    root = tmp_path
    for claim_id, release_id, profile_domain in (
        ("claim-old", "release-old", "labtrust"),
        ("claim-new", "release-new", "agent_tool_use"),
    ):
        claim_dir = root / "corpus" / "pcs" / "claims" / claim_id
        claim_dir.mkdir(parents=True)
        (claim_dir / "lineage.json").write_text(
            json.dumps(
                {
                    "claim_id": claim_id,
                    "release_id": release_id,
                    "signed_bundle_hash": "sha256:" + ("a" * 64),
                    "artifact_hashes": {},
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        (claim_dir / "workflow_profile.json").write_text(
            json.dumps({"workflow_id": f"{profile_domain}.v0", "domain": profile_domain}, indent=2)
            + "\n",
            encoding="utf-8",
        )
        checks = (
            [{"check_id": "manifest_integrity", "status": "passed"}]
            if claim_id == "claim-old"
            else [{"check_id": "manifest_integrity", "status": "failed"}]
        )
        (claim_dir / "release_chain_validation.json").write_text(
            json.dumps(
                {"checks": checks, "deferred_registry_checks": []},
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

    _write_claim_index(
        root,
        [
            {
                "claim_id": "claim-old",
                "claim_dir": "claim-old",
                "release_id": "release-old",
                "imported_at": "2026-01-01T00:00:00Z",
            },
            {
                "claim_id": "claim-new",
                "claim_dir": "claim-new",
                "release_id": "release-new",
                "imported_at": "2026-02-01T00:00:00Z",
            },
        ],
    )

    result = compare_releases(root, old_release_id="release-old", new_release_id="release-new")
    assert result["changed_workflow_profile"]
    assert any(row["field"] == "domain" for row in result["changed_workflow_profile"])
    assert result["changed_registry_checks"]
