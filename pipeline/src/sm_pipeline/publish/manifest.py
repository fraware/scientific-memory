import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

from sm_pipeline.formalize.lean_deps import extract_dependency_ids_for_cards
from sm_pipeline.formalize.theorem_cards import derive_theorem_cards
from sm_pipeline.models.artifact_manifest import ArtifactManifest, CoverageMetrics


def publish_manifest(repo_root: Path, paper_id: str) -> None:
    """Write or update manifest.json and theorem_cards.json from corpus and mapping."""
    repo_root = repo_root.resolve()
    paper_dir = repo_root / "corpus" / "papers" / paper_id
    if not paper_dir.is_dir():
        raise FileNotFoundError(f"Paper directory not found: {paper_dir}")

    claims_path = paper_dir / "claims.json"
    claims = json.loads(claims_path.read_text(encoding="utf-8")) if claims_path.exists() else []
    mapped = sum(1 for c in claims if c.get("linked_formal_targets"))
    machine_checked = sum(1 for c in claims if c.get("status") == "machine_checked")
    cards = derive_theorem_cards(paper_dir, paper_id)
    cards = _merge_theorem_card_reviewer_fields(paper_dir, cards)
    cards = extract_dependency_ids_for_cards(repo_root, paper_id, cards)
    cards = _enrich_cards_with_kernels(repo_root, cards)
    if cards:
        (paper_dir / "theorem_cards.json").write_text(json.dumps(cards, indent=2), encoding="utf-8")
    kernel_linked_claim_ids = {
        str(c.get("claim_id"))
        for c in cards
        if isinstance(c, dict)
        and c.get("claim_id")
        and isinstance(c.get("executable_links"), list)
        and len(c.get("executable_links")) > 0
    }
    kernel_linked = sum(
        1 for c in claims if isinstance(c, dict) and str(c.get("id")) in kernel_linked_claim_ids
    )
    declaration_index = [c["lean_decl"] for c in cards] if cards else _declaration_index(paper_dir)
    generated_pages = _generated_pages(paper_id, claims, cards)
    existing = _read_existing_manifest(paper_dir)
    kernel_index = existing.get("kernel_index") or _kernel_index_from_corpus(
        repo_root, paper_id, cards
    )
    dependency_graph = existing.get("dependency_graph") or _derive_dependency_graph(cards)
    build_hash = _compute_build_hash(paper_id, declaration_index, cards)

    manifest = ArtifactManifest(
        paper_id=paper_id,
        version="0.1.0",
        build_hash=build_hash,
        coverage_metrics=CoverageMetrics(
            claim_count=len(claims),
            mapped_claim_count=mapped,
            machine_checked_count=machine_checked,
            kernel_linked_count=kernel_linked,
        ),
        generated_pages=generated_pages,
        declaration_index=declaration_index,
        dependency_graph=dependency_graph,
        kernel_index=kernel_index,
    )
    out = manifest.model_dump(mode="json")
    (paper_dir / "manifest.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    _set_first_artifact_at_if_missing(paper_dir)


def _set_first_artifact_at_if_missing(paper_dir: Path) -> None:
    """Set metadata.first_artifact_at to now when first publishing manifest (SPEC 12)."""
    meta_path = paper_dir / "metadata.json"
    if not meta_path.exists():
        return
    try:
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return
    if not isinstance(meta, dict) or meta.get("first_artifact_at"):
        return
    now = datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")
    meta["first_artifact_at"] = now
    meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")


def _kernel_index_from_corpus(repo_root: Path, paper_id: str, cards: list) -> list[str]:
    """If corpus/kernels.json exists, return kernel ids that link to this paper's theorem cards."""
    kernels_path = repo_root / "corpus" / "kernels.json"
    if not kernels_path.exists():
        return []
    card_ids = {str(c.get("id")) for c in cards if isinstance(c, dict) and c.get("id")}
    try:
        kernels = json.loads(kernels_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []
    if not isinstance(kernels, list):
        return []
    result = []
    for k in kernels:
        if not isinstance(k, dict) or not k.get("id"):
            continue
        linked = [str(x) for x in (k.get("linked_theorem_cards") or [])]
        if any(tc in card_ids for tc in linked):
            result.append(str(k["id"]))
    return result


def _compute_build_hash(paper_id: str, declaration_index: list, cards: list) -> str:
    """Compute deterministic build hash from paper id, declaration index, and theorem card file paths."""
    parts = [paper_id]
    if declaration_index:
        parts.extend(sorted(declaration_index))
    if cards:
        paths = sorted(
            (c.get("file_path") or "").strip()
            for c in cards
            if isinstance(c, dict) and (c.get("file_path") or "").strip()
        )
        parts.extend(paths)
    content = "\n".join(parts) if parts else paper_id
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def _derive_dependency_graph(cards: list) -> list[dict[str, str]]:
    """Build dependency_graph from theorem cards' dependency_ids using card IDs."""
    edges = []
    for card in cards:
        if not isinstance(card, dict):
            continue
        card_id = card.get("id")
        dep_ids = card.get("dependency_ids") or []
        if not card_id or not isinstance(dep_ids, list):
            continue
        for dep_id in dep_ids:
            if isinstance(dep_id, str) and dep_id.strip():
                edges.append({"from": dep_id.strip(), "to": str(card_id)})
    return edges


def _merge_theorem_card_reviewer_fields(paper_dir: Path, cards: list[dict]) -> list[dict]:
    """Preserve reviewer_status and notes from existing theorem_cards.json on republish."""
    path = paper_dir / "theorem_cards.json"
    if not path.exists() or not cards:
        return cards
    try:
        old = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return cards
    if not isinstance(old, list):
        return cards

    def key(c: dict) -> tuple[str, str]:
        return (str(c.get("claim_id") or ""), str(c.get("lean_decl") or ""))

    old_by_key = {key(c): c for c in old if isinstance(c, dict)}
    for c in cards:
        if not isinstance(c, dict):
            continue
        o = old_by_key.get(key(c))
        if not o:
            continue
        if o.get("reviewer_status") is not None:
            c["reviewer_status"] = o["reviewer_status"]
        if o.get("notes"):
            c["notes"] = o["notes"]
    return cards


def _read_existing_manifest(paper_dir: Path) -> dict:
    """Read existing manifest to preserve kernel_index and dependency_graph."""
    p = paper_dir / "manifest.json"
    if not p.exists():
        return {}
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (json.JSONDecodeError, OSError):
        return {}


def _declaration_index(paper_dir: Path) -> list[str]:
    """Collect declaration names from theorem_cards or existing manifest."""
    cards_path = paper_dir / "theorem_cards.json"
    if cards_path.exists():
        data = json.loads(cards_path.read_text(encoding="utf-8"))
        if isinstance(data, list):
            return [c.get("lean_decl") for c in data if isinstance(c, dict) and c.get("lean_decl")]
    manifest_path = paper_dir / "manifest.json"
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if isinstance(manifest, dict):
            return manifest.get("declaration_index") or []
    return []


def _generated_pages(paper_id: str, claims: list, cards: list) -> list[str]:
    """Build generated_pages: paper, each claim, each theorem card."""
    pages = [f"/papers/{paper_id}"]
    for c in claims:
        if isinstance(c, dict) and c.get("id"):
            pages.append(f"/claims/{c['id']}")
    for card in cards:
        if isinstance(card, dict) and card.get("id"):
            pages.append(f"/theorem-cards/{card['id']}")
    return pages


def _enrich_cards_with_kernels(repo_root: Path, cards: list[dict]) -> list[dict]:
    kernels_path = repo_root / "corpus" / "kernels.json"
    if not kernels_path.exists():
        return cards
    try:
        kernels = json.loads(kernels_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return cards
    if not isinstance(kernels, list):
        return cards

    by_card: dict[str, set[str]] = {}
    for kernel in kernels:
        if not isinstance(kernel, dict) or not kernel.get("id"):
            continue
        kid = str(kernel["id"])
        linked = [str(x) for x in (kernel.get("linked_theorem_cards") or [])]
        for card_id in linked:
            by_card.setdefault(card_id, set()).add(kid)

    enriched: list[dict] = []
    for card in cards:
        if not isinstance(card, dict):
            continue
        card_id = str(card.get("id") or "")
        links = set(str(x) for x in (card.get("executable_links") or []) if str(x))
        links.update(by_card.get(card_id, set()))
        card["executable_links"] = sorted(links)
        enriched.append(card)
    return enriched
