#!/usr/bin/env python3
"""Generate docs/status/repo-snapshot.md from corpus manifests (do not hand-edit output)."""

from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    index_path = repo_root / "corpus" / "index.json"
    if not index_path.exists():
        print("corpus/index.json not found", file=sys.stderr)
        return 1
    index = json.loads(index_path.read_text(encoding="utf-8"))
    papers = index.get("papers") or []
    lines: list[str] = [
        "# Repository snapshot",
        "",
        "**Generated:** do not edit by hand. Regenerate with `just repo-snapshot`.",
        "",
        f"**Generated at (UTC):** {datetime.now(UTC).strftime('%Y-%m-%dT%H:%M:%SZ')}",
        "",
        "| Paper ID | Machine-checked declarations |",
        "|----------|-------------------------------|",
    ]
    total = 0
    for p in sorted(papers, key=lambda x: str(x.get("id") or "")):
        if not isinstance(p, dict):
            continue
        pid = str(p.get("id") or "").strip()
        if not pid:
            continue
        mpath = repo_root / "corpus" / "papers" / pid / "manifest.json"
        n = 0
        if mpath.exists():
            try:
                m = json.loads(mpath.read_text(encoding="utf-8"))
                cm = m.get("coverage_metrics") or {}
                n = int(cm.get("machine_checked_count") or 0)
            except (json.JSONDecodeError, OSError, TypeError, ValueError):
                n = 0
        total += n
        lines.append(f"| `{pid}` | {n} |")
    lines.extend(
        [
            "",
            f"**Total machine-checked declarations (sum of manifests):** {total}",
            "",
        ]
    )
    out = repo_root / "docs" / "status" / "repo-snapshot.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
