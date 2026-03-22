"""Reviewer-status metrics derived from theorem_cards.json artifacts."""

import json
from pathlib import Path


ALLOWED_REVIEWER_STATUS = {"unreviewed", "reviewed", "blocked", "accepted"}


def compute_reviewer_status_metrics(repo_root: Path) -> dict:
    repo_root = repo_root.resolve()
    papers_dir = repo_root / "corpus" / "papers"
    report: dict = {
        "total_cards": 0,
        "by_status": {k: 0 for k in sorted(ALLOWED_REVIEWER_STATUS)},
        "missing_reviewer_status": 0,
        "invalid_reviewer_status": 0,
        "blocked_without_notes": 0,
        "accepted_without_machine_checked": 0,
        "machine_checked_but_unreviewed": 0,
        "per_paper": {},
    }
    if not papers_dir.is_dir():
        return report

    for paper_dir in sorted(papers_dir.iterdir()):
        if not paper_dir.is_dir():
            continue
        path = paper_dir / "theorem_cards.json"
        if not path.exists():
            continue
        try:
            cards = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        if not isinstance(cards, list):
            continue

        p = {
            "total_cards": 0,
            "by_status": {k: 0 for k in sorted(ALLOWED_REVIEWER_STATUS)},
            "missing_reviewer_status": 0,
            "invalid_reviewer_status": 0,
            "blocked_without_notes": 0,
            "accepted_without_machine_checked": 0,
            "machine_checked_but_unreviewed": 0,
        }

        for c in cards:
            if not isinstance(c, dict):
                continue
            report["total_cards"] += 1
            p["total_cards"] += 1
            rs = c.get("reviewer_status")
            rs_s = str(rs) if rs is not None else ""
            if not rs_s:
                report["missing_reviewer_status"] += 1
                p["missing_reviewer_status"] += 1
                continue
            if rs_s not in ALLOWED_REVIEWER_STATUS:
                report["invalid_reviewer_status"] += 1
                p["invalid_reviewer_status"] += 1
                continue
            report["by_status"][rs_s] += 1
            p["by_status"][rs_s] += 1

            if rs_s == "blocked" and not str(c.get("notes") or "").strip():
                report["blocked_without_notes"] += 1
                p["blocked_without_notes"] += 1
            if rs_s == "accepted" and str(c.get("proof_status") or "") != "machine_checked":
                report["accepted_without_machine_checked"] += 1
                p["accepted_without_machine_checked"] += 1
            if rs_s == "unreviewed" and str(c.get("proof_status") or "") == "machine_checked":
                report["machine_checked_but_unreviewed"] += 1
                p["machine_checked_but_unreviewed"] += 1

        report["per_paper"][paper_dir.name] = p

    return report
