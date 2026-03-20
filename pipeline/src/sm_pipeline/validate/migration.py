"""Schema migration note validation (Gate 2): contributor-playbook.md must document migrations."""

import re
from pathlib import Path


class MigrationDocError(Exception):
    """Raised when migration documentation check fails."""

    pass


def validate_migration_doc(repo_root: Path) -> None:
    """
    Enforce that docs/contributor-playbook.md exists and contains a Migration notes section
    with at least one dated entry (e.g. "**2026-03**" or "- **202").
    """
    repo_root = repo_root.resolve()
    doc_path = repo_root / "docs" / "contributor-playbook.md"
    if not doc_path.exists():
        raise MigrationDocError("docs/contributor-playbook.md is missing")
    text = doc_path.read_text(encoding="utf-8")
    if "Migration notes" not in text and "migration notes" not in text.lower():
        raise MigrationDocError(
            "docs/contributor-playbook.md must contain a 'Migration notes' section"
        )
    # Require at least one dated migration note (pattern: - **YYYY-MM** or **YYYY-MM**)
    if not re.search(r"(\*\*20\d{2}-\d{2}\*\*|- \*\*20\d{2})", text):
        raise MigrationDocError(
            "docs/contributor-playbook.md must contain at least one dated migration note (e.g. **2026-03**)"
        )
