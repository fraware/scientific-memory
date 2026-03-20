"""
Canonical publication entry points.

All paper-level manifest/theorem-card regeneration should go through this module so
the repo-wide portal export stays in sync with a single code path.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from sm_pipeline.publish.export_portal_data import export_portal_data
from sm_pipeline.publish.manifest import publish_manifest


def publish_paper_artifacts(repo_root: Path, paper_id: str) -> dict[str, Any]:
    """
    Regenerate manifest and theorem cards for one paper, then refresh the portal bundle.

    Returns paths and ids for logging and tests.
    """
    repo_root = repo_root.resolve()
    publish_manifest(repo_root, paper_id)
    export_path = export_portal_data(repo_root)
    return {
        "paper_id": paper_id,
        "portal_export_path": str(export_path),
    }
