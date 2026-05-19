#!/usr/bin/env python3
"""Sync computation-release fixtures from pcs-core or regenerate via bootstrap."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PCS_CORE = REPO_ROOT.parent / "pcs-core" / "examples" / "computation-release"
FIXTURE_DIR = REPO_ROOT / "tests" / "pcs" / "fixtures" / "computation-release"
REJECTED_FIXTURE_DIR = REPO_ROOT / "tests" / "pcs" / "fixtures" / "computation-rejected-release"
EXAMPLES_DIR = REPO_ROOT / "examples" / "computation-release"
MANIFEST_NAMES = ("release_manifest.v0.json", "ReleaseManifest.v0.json")


def _resolve_manifest(release_dir: Path) -> Path | None:
    for name in MANIFEST_NAMES:
        candidate = release_dir / name
        if candidate.is_file():
            return candidate
    return None


def sync_from_pcs_core(
    pcs_core_dir: Path,
    *,
    fixture_dir: Path,
    examples_dir: Path,
) -> None:
    manifest = _resolve_manifest(pcs_core_dir)
    if manifest is None:
        print(f"error: missing computation release manifest in {pcs_core_dir}", file=sys.stderr)
        raise SystemExit(1)

    for target in (fixture_dir, examples_dir):
        target.mkdir(parents=True, exist_ok=True)
        for path in sorted(pcs_core_dir.iterdir()):
            if path.is_file():
                shutil.copy2(path, target / path.name)
        print(f"synced computation release -> {target}")


def _verify_fixtures() -> bool:
    result = subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / "verify_computation_release_fixture.py")],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        if result.stderr.strip():
            print(result.stderr.strip(), file=sys.stderr)
        return False
    return True


def _bootstrap() -> None:
    print("note: bootstrapping SM computation-release fixtures")
    subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / "bootstrap_computation_release_fixture.py")],
        check=True,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pcs-core-dir", type=Path, default=DEFAULT_PCS_CORE)
    parser.add_argument("--fixture-dir", type=Path, default=FIXTURE_DIR)
    parser.add_argument("--examples-dir", type=Path, default=EXAMPLES_DIR)
    parser.add_argument(
        "--bootstrap-if-missing",
        action="store_true",
        help="Bootstrap when pcs-core example is absent or fails verification after sync",
    )
    parser.add_argument(
        "--write-phase2",
        action="store_true",
        help="Rewrite .phase2-read-model.json after sync/bootstrap",
    )
    args = parser.parse_args()
    pcs_core_dir = args.pcs_core_dir.resolve()

    if _resolve_manifest(pcs_core_dir) is not None:
        sync_from_pcs_core(
            pcs_core_dir,
            fixture_dir=args.fixture_dir.resolve(),
            examples_dir=args.examples_dir.resolve(),
        )
        if not _verify_fixtures():
            if args.bootstrap_if_missing:
                _bootstrap()
            else:
                print(
                    "error: pcs-core computation-release failed SM verification; "
                    "run: just bootstrap-computation-release",
                    file=sys.stderr,
                )
                return 1
    elif args.bootstrap_if_missing:
        _bootstrap()
    else:
        print(
            f"error: missing pcs-core computation-release at {pcs_core_dir}; "
            "pass --bootstrap-if-missing or run: just bootstrap-computation-release",
            file=sys.stderr,
        )
        return 1

    if args.write_phase2:
        sys.path.insert(0, str(REPO_ROOT / "scripts"))
        from pcs_phase2_fixture import write_phase2_read_model_fixture

        for release_dir in (args.fixture_dir.resolve(), REJECTED_FIXTURE_DIR.resolve()):
            if _resolve_manifest(release_dir) is not None:
                out = write_phase2_read_model_fixture(release_dir, repo_root=REPO_ROOT)
                print(f"wrote portal contract fixture -> {out}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
