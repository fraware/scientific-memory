"""Migration doc validation tests (Gate 2)."""

import tempfile
from pathlib import Path

import pytest

from sm_pipeline.validate.migration import MigrationDocError, validate_migration_doc


def test_missing_migration_doc_raises() -> None:
    """Validation fails when docs/contributor-playbook.md is missing."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "docs").mkdir(parents=True)
        with pytest.raises(MigrationDocError, match="missing"):
            validate_migration_doc(root)


def test_migration_doc_without_section_raises() -> None:
    """Validation fails when the doc has no Migration notes section."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "docs").mkdir(parents=True)
        (root / "docs" / "contributor-playbook.md").write_text(
            "# Contributor playbook\n\nSome text.\n",
            encoding="utf-8",
        )
        with pytest.raises(MigrationDocError, match="Migration notes"):
            validate_migration_doc(root)


def test_migration_doc_without_dated_note_raises() -> None:
    """Validation fails when the doc has no dated migration entry."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "docs").mkdir(parents=True)
        (root / "docs" / "contributor-playbook.md").write_text(
            "# Contributor playbook\n\n## Migration notes\n\nNo dated entries here.\n",
            encoding="utf-8",
        )
        with pytest.raises(MigrationDocError, match="dated migration note"):
            validate_migration_doc(root)


def test_migration_doc_valid_passes() -> None:
    """Validation passes when doc exists with Migration notes and a dated entry."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "docs").mkdir(parents=True)
        (root / "docs" / "contributor-playbook.md").write_text(
            "# Contributor playbook\n\n## Migration notes\n\n- **2026-03**: Example note.\n",
            encoding="utf-8",
        )
        validate_migration_doc(root)


def test_migration_doc_alternative_date_format_passes() -> None:
    """Validation passes with alternative date format (**YYYY-MM**)."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "docs").mkdir(parents=True)
        (root / "docs" / "contributor-playbook.md").write_text(
            "# Contributor playbook\n\n## Migration notes\n\n**2026-03**: Example.\n",
            encoding="utf-8",
        )
        validate_migration_doc(root)
