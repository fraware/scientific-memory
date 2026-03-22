"""One-off helper: assign value_kind to claims for scientific compression policy."""

from __future__ import annotations

import json
from pathlib import Path

# Langmuir: explicit assignments for near-duplicate pairs (012/019, 011/016/018 cluster).
_LANGMUIR = {
    "langmuir_1918_claim_001": "foundational_law",
    "langmuir_1918_claim_002": "foundational_law",
    "langmuir_1918_claim_003": "foundational_law",
    "langmuir_1918_claim_004": "bridge_lemma",
    "langmuir_1918_claim_005": "bridge_lemma",
    "langmuir_1918_claim_006": "bridge_lemma",
    "langmuir_1918_claim_007": "bridge_lemma",
    "langmuir_1918_claim_008": "bridge_lemma",
    "langmuir_1918_claim_009": "bridge_lemma",
    "langmuir_1918_claim_010": "bridge_lemma",
    "langmuir_1918_claim_011": "bridge_lemma",
    "langmuir_1918_claim_012": "foundational_law",
    "langmuir_1918_claim_013": "bridge_lemma",
    "langmuir_1918_claim_014": "bridge_lemma",
    "langmuir_1918_claim_015": "bridge_lemma",
    "langmuir_1918_claim_016": "bridge_lemma",
    "langmuir_1918_claim_017": "bridge_lemma",
    "langmuir_1918_claim_018": "foundational_law",
    "langmuir_1918_claim_019": "bridge_lemma",
    "langmuir_1918_claim_020": "executable_contract",
}


def _default_kind(c: dict) -> str:
    ct = (c.get("claim_type") or "").strip()
    if ct in ("definition", "theorem", "conservation_law"):
        return "foundational_law"
    if ct == "identity":
        return "bridge_lemma"
    return "bridge_lemma"


def _apply_to_claims_file(path: Path, paper_id: str) -> None:
    claims = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(claims, list):
        return
    for c in claims:
        if not isinstance(c, dict):
            continue
        cid = str(c.get("id") or "")
        if paper_id == "langmuir_1918_adsorption" and cid in _LANGMUIR:
            c["value_kind"] = _LANGMUIR[cid]
        elif "value_kind" not in c or not str(c.get("value_kind") or "").strip():
            c["value_kind"] = _default_kind(c)
    path.write_text(json.dumps(claims, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    papers = root / "corpus" / "papers"
    for paper_dir in sorted(papers.iterdir()):
        if not paper_dir.is_dir():
            continue
        path = paper_dir / "claims.json"
        if not path.is_file():
            continue
        _apply_to_claims_file(path, paper_dir.name)

    gold = root / "benchmarks" / "gold"
    if gold.is_dir():
        for paper_dir in sorted(gold.iterdir()):
            if not paper_dir.is_dir():
                continue
            path = paper_dir / "claims.json"
            if path.is_file():
                _apply_to_claims_file(path, paper_dir.name)


if __name__ == "__main__":
    main()
