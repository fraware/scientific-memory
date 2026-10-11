"""Prepare the pinned pcs-core checkout for reproducible editable CI installs.

Temporary packaging-only compatibility shim for upstream pcs-core's
python/pyproject.toml, whose readme points outside its Hatchling project root.
This never changes application source, PCS schemas, or scientific fixtures.

Remove this shim once upstream fixes the Python package metadata and the
pinned source revision has been updated.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

PINNED_PCS_CORE_SHA = "9c971f5f9da8a424924dd8f48d6a3b71a1009e1b"
OLD_README = 'readme = "../README.md"'
NEW_README = 'readme = "README.md"'


def prepare(repo_root: Path) -> None:
    """Check the upstream revision and apply only the known README build fix."""
    upstream = repo_root / "pcs-core"
    project = upstream / "python"
    metadata = project / "pyproject.toml"
    source_readme = upstream / "README.md"
    distribution_readme = project / "README.md"

    if not metadata.is_file() or not source_readme.is_file():
        raise FileNotFoundError("Required pcs-core package metadata/README is missing")

    revision = subprocess.check_output(
        ["git", "-C", str(upstream), "rev-parse", "HEAD"], text=True
    ).strip()
    if revision != PINNED_PCS_CORE_SHA:
        raise RuntimeError(
            f"Unexpected pcs-core revision {revision}; expected {PINNED_PCS_CORE_SHA}. "
            "Review the upstream package metadata before updating this shim."
        )

    original = metadata.read_text(encoding="utf-8")
    occurrences = original.count(OLD_README)
    if occurrences == 1:
        if distribution_readme.exists():
            raise RuntimeError("Unexpected pcs-core/python/README.md; review packaging state")
        updated = original.replace(OLD_README, NEW_README)
        metadata.write_text(updated, encoding="utf-8")
        shutil.copyfile(source_readme, distribution_readme)
        operation = "README relocation compatibility patch"
    elif NEW_README in original and distribution_readme.is_file():
        operation = "upstream packaging already fixed"
    else:
        raise RuntimeError("Unknown pcs-core packaging layout; refusing to patch")

    manifest = {
        "upstream_revision": revision,
        "operation": operation,
        "metadata_sha256": hashlib.sha256(metadata.read_bytes()).hexdigest(),
        "readme_sha256": hashlib.sha256(distribution_readme.read_bytes()).hexdigest(),
    }
    print(json.dumps(manifest, sort_keys=True))


if __name__ == "__main__":
    try:
        prepare(Path(__file__).resolve().parents[1])
    except (FileNotFoundError, RuntimeError, subprocess.CalledProcessError) as error:
        print(f"pcs-core bootstrap failed: {error}", file=sys.stderr)
        raise SystemExit(1) from error
