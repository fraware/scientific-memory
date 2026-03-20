"""Generate llm_lean_proposals.json (suggest-only; human-gated apply via proof-repair-apply)."""

from __future__ import annotations

import json
import time
from datetime import UTC, datetime
from pathlib import Path

from sm_pipeline.llm.json_extract import extract_json_object
from sm_pipeline.llm.prompt_templates import (
    LEAN_PROMPT_TEMPLATE_ID,
    LEAN_SYSTEM,
    LEAN_USER_TEMPLATE,
    lean_prompt_template_sha256,
    sha256_hex,
)
from sm_pipeline.llm.provider import LLMMessage, LLMProvider
from sm_pipeline.llm.source_context import load_json_if_exists
from sm_pipeline.models.llm_proposals import LlmLeanProposalsBundle


def _read_lean_excerpt(repo_root: Path, mapping: dict, *, max_chars: int = 80_000) -> str:
    tf = (mapping.get("target_file") or "").strip()
    if not tf:
        ns = (mapping.get("namespace") or "").strip()
        if ns:
            path_part = ns.replace(".", "/")
            tf = f"formal/{path_part}.lean"
    if not tf:
        return ""
    path = repo_root / tf
    if not path.is_file():
        return f"(Lean file not found at {tf})"
    try:
        raw = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return f"(could not read {tf})"
    return raw[:max_chars]


def generate_llm_lean_proposals(
    repo_root: Path,
    paper_id: str,
    provider: LLMProvider,
    *,
    model: str,
    decl: str | None = None,
    temperature: float = 0.2,
) -> dict:
    repo_root = repo_root.resolve()
    paper_dir = repo_root / "corpus" / "papers" / paper_id
    if not paper_dir.is_dir():
        raise FileNotFoundError(f"Paper not found: {paper_dir}")

    mapping_path = paper_dir / "mapping.json"
    if not mapping_path.is_file():
        raise FileNotFoundError(f"mapping.json required for Lean assist: {mapping_path}")
    mapping = json.loads(mapping_path.read_text(encoding="utf-8"))
    if not isinstance(mapping, dict):
        raise ValueError("mapping.json must be a JSON object")

    claims = load_json_if_exists(paper_dir / "claims.json")
    cards = load_json_if_exists(paper_dir / "theorem_cards.json")
    lean_snip = _read_lean_excerpt(repo_root, mapping)
    mapping_blob = json.dumps(mapping, indent=2)
    claims_blob = json.dumps(claims if claims is not None else [], indent=2)
    cards_blob = json.dumps(cards if cards is not None else [], indent=2)
    decl_hint = decl.strip() if decl and decl.strip() else ""
    focus_section = (
        f"\nFocus on declaration / mapping entry related to short name or claim: {decl_hint!r}.\n"
        if decl_hint
        else ""
    )

    user = LEAN_USER_TEMPLATE.format(
        paper_id=paper_id,
        focus_section=focus_section,
        mapping_blob=mapping_blob,
        claims_blob=claims_blob,
        cards_blob=cards_blob,
        lean_snip=lean_snip,
    )

    messages = [
        LLMMessage(role="system", content=LEAN_SYSTEM),
        LLMMessage(role="user", content=user),
    ]
    t0 = time.perf_counter()
    resp = provider.complete(messages, model=model, temperature=temperature, max_tokens=4096)
    latency = time.perf_counter() - t0
    data = extract_json_object(resp.text)
    data["paper_id"] = paper_id
    data["schema_version"] = "0.1.0"
    data["verification_boundary"] = "human_review_only"
    data.setdefault("proposals", [])
    edit_kind_aliases = {
        "proof_improvement": "proof_repair",
        "proof_fix": "proof_repair",
        "proof_refactor": "proof_repair",
        "new_lemma": "lemma_extraction",
    }
    for p in data["proposals"]:
        if isinstance(p, dict):
            p["paper_id"] = paper_id
            raw_kind = p.get("edit_kind")
            if isinstance(raw_kind, str):
                key = raw_kind.strip().lower()
                p["edit_kind"] = edit_kind_aliases.get(key, key)
    meta_out = {
        "provider": "prime_intellect",
        "model": resp.model,
        "created_at": datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "latency_seconds": round(latency, 3),
        "prompt_tokens": resp.prompt_tokens,
        "completion_tokens": resp.completion_tokens,
        "total_tokens": resp.total_tokens,
        "prompt_template_id": LEAN_PROMPT_TEMPLATE_ID,
        "prompt_template_sha256": lean_prompt_template_sha256(),
        "input_artifact_sha256": {
            "mapping_json": sha256_hex(mapping_blob),
            "claims_json": sha256_hex(claims_blob),
            "theorem_cards_json": sha256_hex(cards_blob),
            "lean_excerpt": sha256_hex(lean_snip),
            "decl_hint": sha256_hex(decl_hint),
        },
    }
    existing_meta = data.get("metadata")
    if isinstance(existing_meta, dict):
        data["metadata"] = {**meta_out, **existing_meta}
    else:
        data["metadata"] = meta_out
    bundle = LlmLeanProposalsBundle.model_validate(data)
    return bundle.model_dump(mode="json")
