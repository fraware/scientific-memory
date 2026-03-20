#!/usr/bin/env python3
"""
Append structured corpus / formal / kernel summary to dist/CHANGELOG.md for releases (SPEC 8.7).

Invoke after `scripts/release_artifacts.sh` has created `dist/CHANGELOG.md` (git log section).
From repo root when packaging:
  uv run python scripts/release_corpus_delta.py
"""

from __future__ import annotations

import hashlib
import json
import sys
from datetime import UTC, datetime
from pathlib import Path


def _manifest_checksum(papers_dir: Path) -> str:
    parts: list[bytes] = []
    for p in sorted(papers_dir.glob("*/manifest.json")):
        parts.append(p.read_bytes())
    return hashlib.sha256(b"".join(parts)).hexdigest()


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    index = json.loads((root / "corpus" / "index.json").read_text(encoding="utf-8"))
    papers = index.get("papers") or []
    paper_ids = [p["id"] for p in papers if isinstance(p, dict) and p.get("id")]
    claim_total = 0
    decl_total = 0
    for pid in paper_ids:
        claims_path = root / "corpus" / "papers" / pid / "claims.json"
        if claims_path.exists():
            claims = json.loads(claims_path.read_text(encoding="utf-8"))
            if isinstance(claims, list):
                claim_total += len(claims)
        man = root / "corpus" / "papers" / pid / "manifest.json"
        if man.exists():
            m = json.loads(man.read_text(encoding="utf-8"))
            decl_total += len(m.get("declaration_index") or [])
    msum = _manifest_checksum(root / "corpus" / "papers")
    kernels_path = root / "corpus" / "kernels.json"
    kernel_summary = "n/a"
    if kernels_path.exists():
        ks = json.loads(kernels_path.read_text(encoding="utf-8"))
        if isinstance(ks, list):
            tested = sum(1 for k in ks if isinstance(k, dict) and k.get("test_status") == "tested")
            kernel_summary = f"{len(ks)} entries, {tested} tested"
    changelog = root / "dist" / "CHANGELOG.md"
    if not changelog.is_file():
        print(
            f"SKIP: {changelog} missing (run scripts/release_artifacts.sh first).",
            file=sys.stderr,
        )
        return 0
    block = f"""
## Release delta ({datetime.now(UTC).strftime("%Y-%m-%d")} UTC)

### Corpus
- Papers: {len(paper_ids)} ({", ".join(paper_ids)})
- Claims (sum): {claim_total}
- Declarations (manifest index sum): {decl_total}
- Manifest bundle SHA-256 (concat all manifest.json): `{msum}`

### Formal
- See `lake build`; declaration count above reflects theorem-card/manifest index.

### Kernels
- {kernel_summary}

### Schema
- Breaking changes: see [docs/contributor-playbook.md#schema-versioning-and-migration-notes](docs/contributor-playbook.md).

---
"""
    changelog.write_text(changelog.read_text(encoding="utf-8") + block, encoding="utf-8")
    print(f"Appended release delta to {changelog}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
