"""Research-value metrics: cross-paper reuse, literature errors, assumptions, kernels (SPEC 12).

Data contracts:
- literature_errors_count: from corpus/papers/<id>/literature_errors.json (array length);
  when absent, placeholder from ADR docs.
- claims_with_clarified_assumptions: claims with non-empty linked_assumptions (from claims.json).
- kernels_with_formally_linked_invariants: kernels in corpus/kernels.json with
  non-empty linked_theorem_cards (formally linked invariants).
"""

import json
from pathlib import Path


def compute_research_value_metrics(repo_root: Path) -> dict:
    """
    From manifests and theorem_cards: declarations that appear as dependency
    targets in more than one paper (reusable foundation); cross-paper reuse count.
    Literature errors from literature_errors.json; claims with clarified assumptions;
    kernels with formally linked theorem cards.
    """
    repo_root = repo_root.resolve()
    papers_dir = repo_root / "corpus" / "papers"
    index_path = repo_root / "corpus" / "index.json"
    if not papers_dir.is_dir() or not index_path.exists():
        return _empty_result()

    index = json.loads(index_path.read_text(encoding="utf-8"))
    paper_list = index.get("papers") or []
    paper_ids = [p["id"] for p in paper_list if isinstance(p, dict) and p.get("id")]

    # decl -> set of paper_ids that reference it (as dependency target)
    decl_to_papers: dict[str, set[str]] = {}
    # decl -> set of paper_ids that declare it (in declaration_index)
    decl_declared_by: dict[str, set[str]] = {}

    for paper_id in paper_ids:
        paper_dir = papers_dir / paper_id
        manifest_path = paper_dir / "manifest.json"
        manifest = {}
        if manifest_path.exists():
            try:
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                if not isinstance(manifest, dict):
                    manifest = {}
            except (json.JSONDecodeError, OSError):
                pass
        decl_index = manifest.get("declaration_index") or []
        if not isinstance(decl_index, list):
            decl_index = []
        for d in decl_index:
            if d:
                decl_declared_by.setdefault(str(d), set()).add(paper_id)

        graph = manifest.get("dependency_graph") or []
        if not graph and (paper_dir / "theorem_cards.json").exists():
            try:
                cards = json.loads((paper_dir / "theorem_cards.json").read_text(encoding="utf-8"))
                if isinstance(cards, list):
                    for c in cards:
                        for dep in c.get("dependency_ids") or []:
                            if dep:
                                graph.append({"from": dep, "to": c.get("lean_decl")})
            except (json.JSONDecodeError, OSError):
                pass
        for e in graph:
            if isinstance(e, dict) and e.get("to"):
                to_decl = str(e["to"])
                decl_to_papers.setdefault(to_decl, set()).add(paper_id)

    # Reusable foundation: declarations used as dependency by more than one paper
    reusable = [decl for decl, papers in decl_to_papers.items() if len(papers) > 1]
    cross_paper_reuse_count = len(reusable)
    reusable_foundation_count = cross_paper_reuse_count

    # Literature errors: from optional literature_errors.json per paper, else ADR placeholder
    literature_errors_count = _count_literature_errors(repo_root, paper_ids, papers_dir)

    # Claims whose assumptions were clarified (linked_assumptions non-empty)
    claims_with_clarified_assumptions = _count_claims_with_linked_assumptions(
        papers_dir, paper_ids
    )

    # Kernels with formally linked invariants (linked_theorem_cards non-empty)
    kernels_with_formally_linked_invariants = _count_kernels_with_linked_cards(
        repo_root
    )

    disputed_after_formalization = _count_disputed_with_formal_targets(
        papers_dir, paper_ids
    )

    return {
        "reusable_foundation_count": reusable_foundation_count,
        "cross_paper_reuse_count": cross_paper_reuse_count,
        "reusable_declarations": sorted(reusable)[:100],
        "literature_errors_count": literature_errors_count,
        "declarations_used_by_multiple_papers": len(reusable),
        "claims_with_clarified_assumptions": claims_with_clarified_assumptions,
        "kernels_with_formally_linked_invariants": kernels_with_formally_linked_invariants,
        "disputed_claims_with_formal_targets": disputed_after_formalization,
    }


def _count_literature_errors(
    repo_root: Path,
    paper_ids: list[str],
    papers_dir: Path,
) -> int:
    """
    Count from optional corpus/papers/<paper_id>/literature_errors.json (array);
    fall back to ADR placeholder when no artifact present.
    """
    total = 0
    any_artifact = False
    for paper_id in paper_ids:
        path = papers_dir / paper_id / "literature_errors.json"
        if not path.exists():
            continue
        any_artifact = True
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(data, list):
                total += len(data)
        except (json.JSONDecodeError, OSError):
            pass
    if any_artifact:
        return total
    return _count_literature_errors_placeholder(repo_root)


def _count_literature_errors_placeholder(repo_root: Path) -> int:
    """
    Placeholder: count ADR files that mention 'error' and 'literature'.
    Used when no literature_errors.json artifacts exist.
    """
    adr_dir = repo_root / "docs" / "adr"
    if not adr_dir.is_dir():
        return 0
    count = 0
    for path in adr_dir.glob("*.md"):
        try:
            text = path.read_text(encoding="utf-8", errors="replace").lower()
            if "literature" in text and "error" in text:
                count += 1
        except OSError:
            pass
    return count


def _count_claims_with_linked_assumptions(papers_dir: Path, paper_ids: list[str]) -> int:
    """Count claims that have at least one linked_assumption (clarified assumptions)."""
    total = 0
    for paper_id in paper_ids:
        claims_path = papers_dir / paper_id / "claims.json"
        if not claims_path.exists():
            continue
        try:
            data = json.loads(claims_path.read_text(encoding="utf-8"))
            if not isinstance(data, list):
                continue
            for c in data:
                if isinstance(c, dict):
                    links = c.get("linked_assumptions") or []
                    if isinstance(links, list) and len(links) > 0:
                        total += 1
        except (json.JSONDecodeError, OSError):
            pass
    return total


def _count_kernels_with_linked_cards(repo_root: Path) -> int:
    """Count kernels in corpus/kernels.json with non-empty linked_theorem_cards."""
    path = repo_root / "corpus" / "kernels.json"
    if not path.exists():
        return 0
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, list):
            return 0
        return sum(
            1
            for k in data
            if isinstance(k, dict)
            and len(k.get("linked_theorem_cards") or []) > 0
        )
    except (json.JSONDecodeError, OSError):
        return 0


def _count_disputed_with_formal_targets(papers_dir: Path, paper_ids: list[str]) -> int:
    """
    Claims marked disputed while still linked to formal targets (SPEC 12:
    disputed-after-formalization signal).
    """
    n = 0
    for paper_id in paper_ids:
        path = papers_dir / paper_id / "claims.json"
        if not path.exists():
            continue
        try:
            claims = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        if not isinstance(claims, list):
            continue
        for c in claims:
            if not isinstance(c, dict):
                continue
            if c.get("status") != "disputed":
                continue
            targets = c.get("linked_formal_targets") or []
            if isinstance(targets, list) and len(targets) > 0:
                n += 1
    return n


def _empty_result() -> dict:
    return {
        "reusable_foundation_count": 0,
        "cross_paper_reuse_count": 0,
        "reusable_declarations": [],
        "literature_errors_count": 0,
        "declarations_used_by_multiple_papers": 0,
        "claims_with_clarified_assumptions": 0,
        "kernels_with_formally_linked_invariants": 0,
        "disputed_claims_with_formal_targets": 0,
    }
