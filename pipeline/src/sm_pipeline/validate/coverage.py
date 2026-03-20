"""Coverage integrity (Gate 4): manifest coverage_metrics must match corpus-derived counts."""

import json
from pathlib import Path


class CoverageIntegrityError(Exception):
    """Raised when manifest coverage does not match corpus state."""

    pass


def validate_coverage(repo_root: Path) -> None:
    """
    Enforce SPEC Gate 4: generated coverage report matches corpus state.
    For each paper with a manifest, recompute expected coverage from claims
    and raise if manifest.coverage_metrics disagrees.
    """
    repo_root = repo_root.resolve()
    papers_dir = repo_root / "corpus" / "papers"
    if not papers_dir.is_dir():
        return

    for paper_dir in sorted(papers_dir.iterdir()):
        if not paper_dir.is_dir():
            continue
        manifest_path = paper_dir / "manifest.json"
        if not manifest_path.exists():
            continue
        manifest = _load_json(manifest_path)
        if not isinstance(manifest, dict):
            continue
        metrics = manifest.get("coverage_metrics")
        if not isinstance(metrics, dict):
            continue

        claims_path = paper_dir / "claims.json"
        if not claims_path.exists():
            raise CoverageIntegrityError(
                f"Paper {paper_dir.name}: manifest exists but claims.json missing"
            )
        claims = _load_json(claims_path)
        if not isinstance(claims, list):
            raise CoverageIntegrityError(f"Paper {paper_dir.name}: claims.json invalid")

        expected_claim_count = len(claims)
        expected_mapped = sum(
            1 for c in claims if isinstance(c, dict) and c.get("linked_formal_targets")
        )
        expected_machine_checked = sum(
            1 for c in claims if isinstance(c, dict) and c.get("status") == "machine_checked"
        )
        expected_kernel_linked = _expected_kernel_linked_count(paper_dir, claims)

        actual_claim = metrics.get("claim_count")
        actual_mapped = metrics.get("mapped_claim_count")
        actual_machine_checked = metrics.get("machine_checked_count")
        actual_kernel_linked = metrics.get("kernel_linked_count")

        if actual_claim != expected_claim_count:
            raise CoverageIntegrityError(
                f"Paper {paper_dir.name}: coverage_metrics.claim_count is {actual_claim}, "
                f"expected {expected_claim_count} from claims.json"
            )
        if actual_mapped != expected_mapped:
            raise CoverageIntegrityError(
                f"Paper {paper_dir.name}: coverage_metrics.mapped_claim_count is {actual_mapped}, "
                f"expected {expected_mapped}"
            )
        if actual_machine_checked != expected_machine_checked:
            raise CoverageIntegrityError(
                f"Paper {paper_dir.name}: coverage_metrics.machine_checked_count is "
                f"{actual_machine_checked}, expected {expected_machine_checked}"
            )
        if actual_kernel_linked != expected_kernel_linked:
            raise CoverageIntegrityError(
                f"Paper {paper_dir.name}: coverage_metrics.kernel_linked_count is "
                f"{actual_kernel_linked}, expected {expected_kernel_linked}"
            )


def _load_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def _expected_kernel_linked_count(paper_dir: Path, claims: list) -> int:
    """
    Compute kernel-linked claims from theorem_cards executable_links when present.

    Fallback for legacy papers: count claims explicitly marked linked_to_kernel.
    """
    cards_path = paper_dir / "theorem_cards.json"
    if cards_path.exists():
        try:
            cards = json.loads(cards_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            cards = []
        if isinstance(cards, list):
            claim_ids = set()
            for card in cards:
                if not isinstance(card, dict):
                    continue
                links = card.get("executable_links") or []
                if isinstance(links, list) and len(links) > 0 and card.get("claim_id"):
                    claim_ids.add(str(card.get("claim_id")))
            return len(claim_ids)

    return sum(1 for c in claims if isinstance(c, dict) and c.get("status") == "linked_to_kernel")
