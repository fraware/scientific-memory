#!/usr/bin/env python3
"""Extract theorem cards from Lean declarations and corpus mapping. Placeholder."""

from pathlib import Path


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    print(f"Repo root: {repo_root}")
    # TODO: parse Lean files, match mapping.json, emit theorem card JSON


if __name__ == "__main__":
    main()
