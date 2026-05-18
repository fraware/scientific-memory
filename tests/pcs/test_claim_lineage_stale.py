"""Staleness detection across all operational signals."""

from __future__ import annotations

from sm_pipeline.pcs_import.claim_lineage import check_stale


def _base_lineage() -> dict:
    return {
        "signed_bundle_hash": "sha256:" + "a" * 64,
        "certificate_id": "cert-trace-abc",
        "trace_hash": "sha256:" + "b" * 64,
        "release_manifest_hash": "sha256:" + "c" * 64,
        "source_commits": {"scientific_memory": "c4259a4cb79fe7b195fd156feb346c08fc334d33"},
        "schema_versions": {"signed_bundle": "v0", "science_claim_bundle": "v0"},
    }


def test_check_stale_signed_bundle_hash() -> None:
    lineage = _base_lineage()
    stale, reasons = check_stale(
        lineage,
        current_bundle_hash="sha256:" + "d" * 64,
    )
    assert stale
    assert any("signed_bundle_hash" in r for r in reasons)


def test_check_stale_certificate_id() -> None:
    lineage = _base_lineage()
    stale, reasons = check_stale(lineage, current_certificate_id="cert-other")
    assert stale
    assert any("certificate_id" in r for r in reasons)


def test_check_stale_trace_hash() -> None:
    lineage = _base_lineage()
    stale, reasons = check_stale(lineage, current_trace_hash="sha256:" + "e" * 64)
    assert stale
    assert any("trace_hash" in r for r in reasons)


def test_check_stale_release_manifest_hash() -> None:
    lineage = _base_lineage()
    stale, reasons = check_stale(
        lineage,
        current_release_manifest_hash="sha256:" + "f" * 64,
    )
    assert stale
    assert any("release_manifest_hash" in r for r in reasons)


def test_check_stale_source_commit() -> None:
    lineage = _base_lineage()
    stale, reasons = check_stale(
        lineage,
        current_source_commits={"scientific_memory": "0" * 40},
    )
    assert stale
    assert any("source_commit" in r for r in reasons)


def test_check_stale_schema_version() -> None:
    lineage = _base_lineage()
    stale, reasons = check_stale(
        lineage,
        current_schema_versions={"signed_bundle": "v1"},
    )
    assert stale
    assert any("schema_version" in r for r in reasons)


def test_check_stale_failed_revalidation() -> None:
    lineage = _base_lineage()
    stale, reasons = check_stale(lineage, validation_status="Rejected")
    assert stale
    assert any("revalidation" in r for r in reasons)


def test_check_stale_fresh_when_unchanged() -> None:
    lineage = _base_lineage()
    stale, reasons = check_stale(
        lineage,
        current_bundle_hash=lineage["signed_bundle_hash"],
        current_certificate_id=lineage["certificate_id"],
        current_trace_hash=lineage["trace_hash"],
        current_release_manifest_hash=lineage["release_manifest_hash"],
        current_source_commits=lineage["source_commits"],
        current_schema_versions=lineage["schema_versions"],
        validation_status="ProofChecked",
    )
    assert not stale
    assert reasons == []
