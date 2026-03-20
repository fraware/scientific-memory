"""Export corpus state as diff baseline (corpus/snapshots/<baseline>.json)."""

import json
from datetime import UTC, datetime
from pathlib import Path


def export_diff_baseline(
    repo_root: Path,
    snapshot_at: str | None = None,
    baseline_id: str = "last-release",
    title: str | None = None,
    narrative: str | None = None,
    highlights: list[str] | None = None,
) -> Path:
    """
    Write baseline snapshot JSON with papers, claim_count, assumption_ids, claim_statuses.
    Used by the portal Diff page to compare current vs baseline.
    """
    repo_root = repo_root.resolve()
    papers_dir = repo_root / "corpus" / "papers"
    index_path = repo_root / "corpus" / "index.json"
    out_dir = repo_root / "corpus" / "snapshots"
    bid = (baseline_id or "last-release").strip().replace("\\", "/")
    bid = bid[:-5] if bid.endswith(".json") else bid
    if "/" in bid or ".." in bid or bid == "":
        raise ValueError(f"Invalid baseline_id: {baseline_id!r}")
    out_path = out_dir / f"{bid}.json"

    if not papers_dir.is_dir():
        raise FileNotFoundError(f"Papers directory not found: {papers_dir}")

    index = {}
    if index_path.exists():
        index = json.loads(index_path.read_text(encoding="utf-8"))
    paper_list = index.get("papers") or []
    paper_ids = [p["id"] for p in paper_list if isinstance(p, dict) and p.get("id")]

    papers_payload = []
    for paper_id in paper_ids:
        paper_dir = papers_dir / paper_id
        if not paper_dir.is_dir():
            continue
        claims_path = paper_dir / "claims.json"
        assumptions_path = paper_dir / "assumptions.json"

        claim_count = 0
        claim_statuses: list[dict[str, str]] = []
        if claims_path.exists():
            claims = json.loads(claims_path.read_text(encoding="utf-8"))
            if isinstance(claims, list):
                claim_count = len(claims)
                for c in claims:
                    if isinstance(c, dict) and c.get("id"):
                        claim_statuses.append(
                            {
                                "id": str(c["id"]),
                                "status": str(c.get("status", "")),
                            }
                        )

        assumption_ids: list[str] = []
        if assumptions_path.exists():
            assumptions = json.loads(assumptions_path.read_text(encoding="utf-8"))
            if isinstance(assumptions, list):
                assumption_ids = [
                    str(a.get("id", "")) for a in assumptions if isinstance(a, dict) and a.get("id")
                ]

        declarations: list[dict[str, str]] = []
        cards_path = paper_dir / "theorem_cards.json"
        if cards_path.exists():
            cards = json.loads(cards_path.read_text(encoding="utf-8"))
            if isinstance(cards, list):
                for card in cards:
                    if isinstance(card, dict) and card.get("lean_decl"):
                        declarations.append(
                            {
                                "lean_decl": str(card["lean_decl"]),
                                "proof_status": str(card.get("proof_status", "")),
                            }
                        )
        if not declarations:
            manifest_path = paper_dir / "manifest.json"
            if manifest_path.exists():
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                decl_index = manifest.get("declaration_index") or []
                if isinstance(decl_index, list):
                    for decl in decl_index:
                        if decl:
                            declarations.append(
                                {
                                    "lean_decl": str(decl),
                                    "proof_status": "",
                                }
                            )

        meta = next(
            (p for p in paper_list if isinstance(p, dict) and p.get("id") == paper_id),
            {},
        )
        papers_payload.append(
            {
                "id": paper_id,
                "title": meta.get("title"),
                "year": meta.get("year"),
                "claim_count": claim_count,
                "assumption_ids": assumption_ids,
                "claim_statuses": claim_statuses,
                "declarations": declarations,
            }
        )

    now = datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")
    payload = {
        "baseline_id": bid,
        "title": title,
        "narrative": narrative,
        "highlights": highlights or [],
        "snapshot_at": snapshot_at or now,
        "papers": papers_payload,
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return out_path
