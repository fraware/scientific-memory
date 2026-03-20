"""Tests for extraction_run.json enforcement (SPEC 8.2)."""

import pytest

from sm_pipeline.validate.extraction_artifacts import (
    ExtractionArtifactError,
    validate_extraction_run_required,
)


def test_validate_extraction_run_required_ok_when_no_claims(tmp_path):
    """Papers with empty claims do not require extraction_run.json."""
    paper_dir = tmp_path / "corpus" / "papers" / "p1"
    paper_dir.mkdir(parents=True)
    (paper_dir / "claims.json").write_text("[]", encoding="utf-8")
    validate_extraction_run_required(tmp_path)


def test_validate_extraction_run_required_ok_when_run_exists(tmp_path):
    """Papers with claims and extraction_run.json pass."""
    paper_dir = tmp_path / "corpus" / "papers" / "p1"
    paper_dir.mkdir(parents=True)
    (paper_dir / "claims.json").write_text('[{"id": "c1"}]', encoding="utf-8")
    (paper_dir / "extraction_run.json").write_text(
        '{"paper_id": "p1", "claim_count": 1}', encoding="utf-8"
    )
    validate_extraction_run_required(tmp_path)


def test_validate_extraction_run_required_raises_when_claims_no_run(tmp_path):
    """Papers with non-empty claims and no extraction_run.json raise."""
    paper_dir = tmp_path / "corpus" / "papers" / "p1"
    paper_dir.mkdir(parents=True)
    (paper_dir / "claims.json").write_text('[{"id": "c1"}]', encoding="utf-8")
    with pytest.raises(ExtractionArtifactError) as exc_info:
        validate_extraction_run_required(tmp_path)
    assert "p1" in str(exc_info.value)
    assert "extraction_run.json" in str(exc_info.value)


def test_validate_extraction_run_required_skips_missing_papers_dir(tmp_path):
    """No error when corpus/papers does not exist."""
    validate_extraction_run_required(tmp_path)
