"""Graph and link integrity validation (Gate 2/3).

Ensures no orphan references across claims, theorem cards, kernels, and manifests.
"""

import json
from pathlib import Path


class GraphIntegrityError(Exception):
    """Raised when graph/link integrity check fails (orphan refs)."""

    pass


def _load_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_graph(repo_root: Path) -> None:
    """
    Enforce SPEC Gate 2/3 link integrity:
    - Every theorem card claim_id references an existing claim in the same paper.
    - Every mapping claim_to_decl key references an existing claim in the same paper.
    - Every theorem card dependency_id references an existing theorem card id
      (within corpus).
    - Every theorem card executable_link and manifest kernel_index references an existing kernel id.
    - Every claim linked_assumption references an existing assumption; every
      linked_symbol references an existing symbol.
    """
    repo_root = repo_root.resolve()
    papers_dir = repo_root / "corpus" / "papers"
    if not papers_dir.is_dir():
        return

    # Build global theorem card id set (all papers) for dependency_id resolution.
    all_theorem_card_ids: set[str] = set()
    paper_theorem_card_ids: dict[str, set[str]] = {}

    # Load kernels once
    kernels_path = repo_root / "corpus" / "kernels.json"
    kernel_ids: set[str] = set()
    if kernels_path.exists():
        raw = kernels_path.read_text(encoding="utf-8").strip()
        if raw:
            data = json.loads(raw)
            if isinstance(data, list):
                for k in data:
                    if isinstance(k, dict) and k.get("id"):
                        kernel_ids.add(str(k["id"]))

    for paper_dir in sorted(papers_dir.iterdir()):
        if not paper_dir.is_dir():
            continue
        paper_id = paper_dir.name
        metadata_path = paper_dir / "metadata.json"
        if not metadata_path.exists():
            continue

        claims_path = paper_dir / "claims.json"
        if not claims_path.exists():
            continue
        claims_data = _load_json(claims_path)
        if not isinstance(claims_data, list):
            continue
        claim_ids = {c["id"] for c in claims_data if isinstance(c, dict) and c.get("id")}

        mapping_path = paper_dir / "mapping.json"
        mapping_data = _load_json(mapping_path) if mapping_path.exists() else {}
        has_mapping_namespace = isinstance(mapping_data, dict) and bool(
            (mapping_data.get("namespace") or "").strip()
        )

        # Theorem cards: claim_id must exist in claims; file_path required when mapping has namespace
        cards_path = paper_dir / "theorem_cards.json"
        if cards_path.exists():
            cards = _load_json(cards_path)
            if isinstance(cards, list):
                paper_card_ids = set()
                for card in cards:
                    if not isinstance(card, dict):
                        continue
                    cid = card.get("claim_id")
                    card_id = card.get("id")
                    if card_id:
                        paper_card_ids.add(str(card_id))
                        all_theorem_card_ids.add(str(card_id))
                    if cid and cid not in claim_ids:
                        raise GraphIntegrityError(
                            f"Theorem card {card.get('id', '?')} in {paper_id} references "
                            f"claim_id {cid} which does not exist in claims.json"
                        )
                    if (
                        has_mapping_namespace
                        and card.get("lean_decl")
                        and not (card.get("file_path") or "").strip()
                    ):
                        raise GraphIntegrityError(
                            f"Theorem card {card.get('id', '?')} in {paper_id} has empty file_path; "
                            "re-run publish-artifacts to populate from mapping"
                        )
                    for dep in card.get("dependency_ids") or []:
                        if not dep:
                            continue
                        # Will check dep in all_theorem_card_ids after we've collected all cards
                        pass
                    for ex in card.get("executable_links") or []:
                        if not ex:
                            continue
                        if len(kernel_ids) > 0 and ex not in kernel_ids:
                            raise GraphIntegrityError(
                                f"Theorem card {card.get('id', '?')} in {paper_id} references "
                                f"executable kernel {ex} which is not in corpus/kernels.json"
                            )
                paper_theorem_card_ids[paper_id] = paper_card_ids
        else:
            paper_theorem_card_ids[paper_id] = set()

        # Mapping: every claim_to_decl key must be in claims
        if mapping_path.exists() and isinstance(mapping_data, dict):
            claim_to_decl = mapping_data.get("claim_to_decl") or {}
            if isinstance(claim_to_decl, dict):
                for mid in claim_to_decl:
                    if mid not in claim_ids:
                        raise GraphIntegrityError(
                            "Mapping in "
                            f"{paper_id} has claim_to_decl key {mid} which "
                            "does not exist in claims.json"
                        )

        # Manifest: kernel_index entries must exist in kernels
        manifest_path = paper_dir / "manifest.json"
        if manifest_path.exists():
            manifest = _load_json(manifest_path)
            if isinstance(manifest, dict):
                for kid in manifest.get("kernel_index") or []:
                    if kid and len(kernel_ids) > 0 and kid not in kernel_ids:
                        raise GraphIntegrityError(
                            f"Manifest in {paper_id} kernel_index references kernel {kid} "
                            "which is not in corpus/kernels.json"
                        )

        # Claims: linked_assumptions and linked_symbols must exist in same paper
        assumptions_path = paper_dir / "assumptions.json"
        assumption_ids: set[str] = set()
        if assumptions_path.exists():
            assumptions = _load_json(assumptions_path)
            if isinstance(assumptions, list):
                assumption_ids = {
                    a["id"] for a in assumptions if isinstance(a, dict) and a.get("id")
                }
        symbols_path = paper_dir / "symbols.json"
        symbol_ids: set[str] = set()
        if symbols_path.exists():
            symbols = _load_json(symbols_path)
            if isinstance(symbols, list):
                symbol_ids = {s["id"] for s in symbols if isinstance(s, dict) and s.get("id")}
        for claim in claims_data:
            if not isinstance(claim, dict):
                continue
            for aid in claim.get("linked_assumptions") or []:
                if aid and assumption_ids and aid not in assumption_ids:
                    raise GraphIntegrityError(
                        f"Claim {claim.get('id', '?')} in {paper_id} "
                        f"references assumption {aid} "
                        "which does not exist in assumptions.json"
                    )
            for sid in claim.get("linked_symbols") or []:
                if sid and symbol_ids and sid not in symbol_ids:
                    raise GraphIntegrityError(
                        f"Claim {claim.get('id', '?')} in {paper_id} "
                        f"references symbol {sid} "
                        "which does not exist in symbols.json"
                    )

    # Second pass: dependency_ids must reference existing theorem card ids (any paper)
    for paper_dir in sorted(papers_dir.iterdir()):
        if not paper_dir.is_dir():
            continue
        paper_id = paper_dir.name
        cards_path = paper_dir / "theorem_cards.json"
        if not cards_path.exists():
            continue
        cards = _load_json(cards_path)
        if not isinstance(cards, list):
            continue
        for card in cards:
            if not isinstance(card, dict):
                continue
            for dep in card.get("dependency_ids") or []:
                if dep and dep not in all_theorem_card_ids:
                    raise GraphIntegrityError(
                        f"Theorem card {card.get('id', '?')} in {paper_id} references "
                        f"dependency_id {dep} which is not a theorem card id in the corpus"
                    )

    # Kernel linked_theorem_cards must reference existing theorem card ids
    if kernels_path.exists():
        raw = kernels_path.read_text(encoding="utf-8").strip()
        if raw:
            try:
                kernels_data = json.loads(raw)
            except json.JSONDecodeError:
                kernels_data = []
            if isinstance(kernels_data, list):
                for k in kernels_data:
                    if not isinstance(k, dict) or not k.get("id"):
                        continue
                    for card_id in k.get("linked_theorem_cards") or []:
                        if card_id and card_id not in all_theorem_card_ids:
                            raise GraphIntegrityError(
                                f"Kernel {k.get('id')} references theorem card {card_id} "
                                "which is not a theorem card id in the corpus"
                            )


def validate_dependency_graph_bootstrap_warn(repo_root: Path) -> list[str]:
    """
    Non-blocking: flag papers where multiple theorem cards exist but all dependency_ids are empty
    while at least one claim is machine_checked (Tier-0 extractor may yield an empty graph).
    """
    repo_root = repo_root.resolve()
    papers_dir = repo_root / "corpus" / "papers"
    if not papers_dir.is_dir():
        return []
    warnings: list[str] = []
    for paper_dir in sorted(papers_dir.iterdir()):
        if not paper_dir.is_dir():
            continue
        paper_id = paper_dir.name
        cards_path = paper_dir / "theorem_cards.json"
        if not cards_path.exists():
            continue
        try:
            cards = _load_json(cards_path)
        except (json.JSONDecodeError, OSError):
            continue
        if not isinstance(cards, list) or len(cards) < 2:
            continue
        # Two independent theorems in one file are common; do not hint "empty graph".
        if len(cards) == 2:
            continue
        if any((isinstance(c, dict) and (c.get("dependency_ids") or [])) for c in cards):
            continue
        claims_path = paper_dir / "claims.json"
        if not claims_path.exists():
            continue
        try:
            claims = _load_json(claims_path)
        except (json.JSONDecodeError, OSError):
            continue
        if not isinstance(claims, list):
            continue
        if not any(isinstance(c, dict) and c.get("status") == "machine_checked" for c in claims):
            continue
        warnings.append(
            f"{paper_id}: {len(cards)} theorem cards but no dependency_ids "
            f"(dependency_extraction_method is bootstrap regex; graph may be empty)"
        )
    return warnings


def validate_dependency_graph_quality_warn(repo_root: Path) -> list[str]:
    """
    Warn-only graph quality checks (SPEC 8.x graph quality metrics).

    Metrics (per paper):
    - edge_density: average dependency_ids per theorem card
    - sparse_ratio: fraction of theorem cards with empty dependency_ids

    Because current dependency extraction is heuristic, this is not enforced as a hard gate yet.
    """

    repo_root = repo_root.resolve()
    papers_dir = repo_root / "corpus" / "papers"
    if not papers_dir.is_dir():
        return []

    warnings: list[str] = []
    for paper_dir in sorted(papers_dir.iterdir()):
        if not paper_dir.is_dir():
            continue
        paper_id = paper_dir.name
        cards_path = paper_dir / "theorem_cards.json"
        if not cards_path.exists():
            continue

        try:
            cards = _load_json(cards_path)
        except Exception:
            continue

        if not isinstance(cards, list) or not cards:
            continue

        dep_counts: list[int] = []
        empty_count = 0
        for c in cards:
            if not isinstance(c, dict):
                continue
            deps = c.get("dependency_ids") or []
            if not isinstance(deps, list):
                deps = []
            dep_counts.append(len(deps))
            if len(deps) == 0:
                empty_count += 1

        if not dep_counts:
            continue

        total_cards = len(dep_counts)
        edge_density = sum(dep_counts) / total_cards
        sparse_ratio = empty_count / total_cards

        # Thresholds tuned for warn-only behavior. Once tier-1 is stable across papers,
        # we can promote this to an acceptance gate.
        if total_cards >= 6 and sparse_ratio >= 0.60:
            warnings.append(
                f"Dependency graph quality (warn): {paper_id} edge_density={edge_density:.2f}, "
                f"sparse_ratio={sparse_ratio:.2f} (>=60% cards with empty dependency_ids)"
            )
        elif total_cards >= 6 and edge_density <= 0.25 and sparse_ratio >= 0.40:
            warnings.append(
                f"Dependency graph quality (warn): {paper_id} edge_density={edge_density:.2f}, "
                f"sparse_ratio={sparse_ratio:.2f} (edge density very low)"
            )

    return warnings
