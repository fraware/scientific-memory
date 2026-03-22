"""Reviewer workflow validation (v0.2): disputed claims must have review_notes; lifecycle and audit checks."""

import json
import re
from pathlib import Path
from itertools import combinations


# Allowed claim status values (must match common.schema.json $defs.status).
ALLOWED_CLAIM_STATUSES = frozenset(
    {
        "unparsed",
        "parsed",
        "mapped",
        "stubbed",
        "compiles_with_sorries",
        "machine_checked",
        "linked_to_kernel",
        "disputed",
        "superseded",
    }
)


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


REUSE_VALUE_KINDS = frozenset(
    {
        "foundational_law",
        "bridge_lemma",
        "executable_contract",
        "cross_paper_anchor",
    }
)


def _normalize_claim_tokens(text: str) -> set[str]:
    """
    Best-effort deterministic token normalization for near-duplicate detection.

    This is intentionally conservative and only aims to catch obvious algebraic variants
    inside a single paper, not semantic equivalence.
    """

    tokens = re.findall(r"[a-zA-Z0-9_]+", (text or "").lower())
    return set(tokens)


def _claim_signature(c: dict) -> tuple:
    """Group key for near-duplicate detection within a paper."""

    claim_type = c.get("claim_type") or ""
    linked_symbols = c.get("linked_symbols") or []
    linked_assumptions = c.get("linked_assumptions") or []
    return (
        str(claim_type),
        tuple(sorted(map(str, linked_symbols))),
        tuple(sorted(map(str, linked_assumptions))),
    )


def _jaccard(a: set[str], b: set[str]) -> float:
    if not a and not b:
        return 0.0
    union = a | b
    if not union:
        return 0.0
    return len(a & b) / len(union)


def _compute_near_duplicate_candidates(
    claims: list[dict], *, jaccard_threshold: float
) -> list[dict]:
    """
    Return candidate near-duplicate pairs within a paper.

    A pair is considered near-duplicate when:
    - both claims share the same signature (claim_type plus linked_symbols and linked_assumptions), and
    - their normalized informal_text token sets have Jaccard similarity >= jaccard_threshold.
    """

    by_sig: dict[tuple, list[dict]] = {}
    for c in claims:
        if not isinstance(c, dict):
            continue
        sig = _claim_signature(c)
        by_sig.setdefault(sig, []).append(c)

    pairs: list[dict] = []
    for _, group in by_sig.items():
        if len(group) < 2:
            continue
        for a, b in combinations(group, 2):
            a_text = a.get("informal_text") or ""
            b_text = b.get("informal_text") or ""
            a_tokens = _normalize_claim_tokens(a_text)
            b_tokens = _normalize_claim_tokens(b_text)
            sim = _jaccard(a_tokens, b_tokens)
            if sim >= jaccard_threshold:
                pairs.append(
                    {
                        "claim_id_a": a.get("id"),
                        "claim_id_b": b.get("id"),
                        "similarity": sim,
                        "value_kind_a": a.get("value_kind"),
                        "value_kind_b": b.get("value_kind"),
                    }
                )
    return pairs


def validate_claim_value_policy(repo_root: Path, *, jaccard_threshold: float = 0.75) -> None:
    """
    Reject near-duplicate algebraic variants unless at least one claim carries explicit reuse value.

    Enforcement is incremental for backward compatibility:
    - Only enforce when BOTH claims have `value_kind` present.
    - If neither claim carries an explicit reuse value kind, raise.
    - If one or both claims are missing `value_kind`, skip enforcement for that pair.
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

        pairs = _compute_near_duplicate_candidates(claims, jaccard_threshold=jaccard_threshold)
        for p in pairs:
            ak = p.get("value_kind_a")
            bk = p.get("value_kind_b")
            if not ak or not bk:
                continue  # classification missing; skip enforcement

            if ak not in REUSE_VALUE_KINDS and bk not in REUSE_VALUE_KINDS:
                raise ReviewerWorkflowError(
                    f"Near-duplicate claim variants in {paper_dir.name}: "
                    f"{p['claim_id_a']} and {p['claim_id_b']} (similarity={p['similarity']:.2f}) "
                    "both lack explicit reuse value_kind. "
                    f"Mark at least one claim with a reuse value_kind in {sorted(REUSE_VALUE_KINDS)} "
                    "or revise informal_text and links to remove duplication."
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
        "claim_value_kind_distribution": {},
        "near_duplicate_claim_pairs_without_explicit_reuse": [],
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
            report["claims_by_status"].setdefault(status, []).append(
                {"paper_id": paper_id, "claim_id": cid}
            )
            if status not in ALLOWED_CLAIM_STATUSES:
                report["invalid_status_claims"].append(
                    {"paper_id": paper_id, "claim_id": cid, "status": status}
                )
            if status == "disputed":
                if (c.get("review_notes") or "").strip():
                    report["disputed_with_notes"].append({"paper_id": paper_id, "claim_id": cid})
                else:
                    report["disputed_without_notes"].append({"paper_id": paper_id, "claim_id": cid})

            vk = (c.get("value_kind") or "").strip()
            if vk:
                report["claim_value_kind_distribution"][vk] = (
                    report["claim_value_kind_distribution"].get(vk, 0) + 1
                )

        # Visibility for near-duplicate candidates. Enforcement happens in validate_claim_value_policy.
        pairs = _compute_near_duplicate_candidates(claims, jaccard_threshold=0.75)
        for p in pairs:
            ak = p.get("value_kind_a")
            bk = p.get("value_kind_b")
            if not ak or not bk:
                continue
            if ak not in REUSE_VALUE_KINDS and bk not in REUSE_VALUE_KINDS:
                report["near_duplicate_claim_pairs_without_explicit_reuse"].append(
                    {
                        "paper_id": paper_id,
                        "claim_id_a": p.get("claim_id_a"),
                        "claim_id_b": p.get("claim_id_b"),
                        "similarity": p.get("similarity"),
                        "value_kind_a": ak,
                        "value_kind_b": bk,
                    }
                )

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
