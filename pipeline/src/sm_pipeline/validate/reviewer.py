"""Reviewer workflow validation (v0.2): disputed claims must have review_notes; lifecycle and audit checks."""

import json
from pathlib import Path


# Allowed claim status values (must match common.schema.json $defs.status).
ALLOWED_CLAIM_STATUSES = frozenset({
    "unparsed", "parsed", "mapped", "stubbed", "compiles_with_sorries",
    "machine_checked", "linked_to_kernel", "disputed", "superseded",
})


class ReviewerWorkflowError(Exception):
    """Raised when reviewer workflow check fails."""

    pass


def validate_reviewer_workflow(repo_root: Path) -> None:
    """
    Enforce that claims with status 'disputed' have non-empty review_notes
    (justification for the dispute).
    """
    repo_root = repo_root.resolve()
    papers_dir = repo_root / "corpus" / "papers"
    if not papers_dir.is_dir():
        return

    for paper_dir in sorted(papers_dir.iterdir()):
        if not paper_dir.is_dir():
            continue
        claims_path = paper_dir / "claims.json"
        if not claims_path.exists():
            continue
        try:
            claims = json.loads(claims_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        if not isinstance(claims, list):
            continue
        for c in claims:
            if not isinstance(c, dict):
                continue
            if (c.get("status") or "").strip() != "disputed":
                continue
            notes = (c.get("review_notes") or "").strip()
            if not notes:
                raise ReviewerWorkflowError(
                    f"Claim {c.get('id', '?')} in {paper_dir.name} has status 'disputed' "
                    "but no review_notes; add justification when disputing"
                )


def compute_reviewer_report(repo_root: Path) -> dict:
    """
    Build a machine-readable reviewer report: claims by status, disputed with/without notes,
    invalid statuses. Does not raise; use for visibility and CI reporting.
    """
    repo_root = repo_root.resolve()
    papers_dir = repo_root / "corpus" / "papers"
    report: dict = {
        "claims_by_status": {},
        "disputed_with_notes": [],
        "disputed_without_notes": [],
        "invalid_status_claims": [],
    }
    if not papers_dir.is_dir():
        return report

    for paper_dir in sorted(papers_dir.iterdir()):
        if not paper_dir.is_dir():
            continue
        claims_path = paper_dir / "claims.json"
        if not claims_path.exists():
            continue
        try:
            claims = json.loads(claims_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        if not isinstance(claims, list):
            continue
        paper_id = paper_dir.name
        for c in claims:
            if not isinstance(c, dict):
                continue
            cid = c.get("id", "?")
            status = (c.get("status") or "").strip() or "unparsed"
            report["claims_by_status"].setdefault(status, []).append({"paper_id": paper_id, "claim_id": cid})
            if status not in ALLOWED_CLAIM_STATUSES:
                report["invalid_status_claims"].append({"paper_id": paper_id, "claim_id": cid, "status": status})
            if status == "disputed":
                if (c.get("review_notes") or "").strip():
                    report["disputed_with_notes"].append({"paper_id": paper_id, "claim_id": cid})
                else:
                    report["disputed_without_notes"].append({"paper_id": paper_id, "claim_id": cid})

    return report


def validate_reviewer_lifecycle(repo_root: Path) -> None:
    """
    Enforce reviewer lifecycle rules: all claim statuses must be allowed;
    disputed claims must have non-empty review_notes. Raises ReviewerWorkflowError on violation.
    """
    report = compute_reviewer_report(repo_root)
    if report["invalid_status_claims"]:
        first = report["invalid_status_claims"][0]
        raise ReviewerWorkflowError(
            f"Claim {first['claim_id']} in {first['paper_id']} has invalid status '{first['status']}'; "
            f"allowed: {sorted(ALLOWED_CLAIM_STATUSES)}"
        )
    if report["disputed_without_notes"]:
        first = report["disputed_without_notes"][0]
        raise ReviewerWorkflowError(
            f"Claim {first['claim_id']} in {first['paper_id']} has status 'disputed' but no review_notes"
        )
