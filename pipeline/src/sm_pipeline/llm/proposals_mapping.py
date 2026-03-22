"""Generate llm_mapping_proposals.json (suggest-only)."""

from __future__ import annotations

import json
import time
from datetime import UTC, datetime
from pathlib import Path

from sm_pipeline.llm.json_extract import extract_json_object
from sm_pipeline.llm.prompt_templates import (
    MAPPING_PROMPT_TEMPLATE_ID,
    MAPPING_SYSTEM,
    MAPPING_USER_TEMPLATE,
    mapping_prompt_template_sha256,
    sha256_hex,
)
from sm_pipeline.llm.provider import LLMMessage, LLMProvider
from sm_pipeline.models.llm_proposals import LlmMappingProposalsBundle


def _read_lean_snippet(repo_root: Path, mapping: dict, max_chars: int = 24_000) -> str:
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


def generate_llm_mapping_proposals(
    repo_root: Path,
    paper_id: str,
    provider: LLMProvider,
    *,
    model: str,
    temperature: float = 0.2,
) -> dict:
    repo_root = repo_root.resolve()
    paper_dir = repo_root / "corpus" / "papers" / paper_id
    if not paper_dir.is_dir():
        raise FileNotFoundError(f"Paper not found: {paper_dir}")

    mapping_path = paper_dir / "mapping.json"
    if not mapping_path.is_file():
        raise FileNotFoundError(f"mapping.json required: {mapping_path}")
    mapping = json.loads(mapping_path.read_text(encoding="utf-8"))
    claims = json.loads((paper_dir / "claims.json").read_text(encoding="utf-8"))
    lean_snip = _read_lean_snippet(repo_root, mapping if isinstance(mapping, dict) else {})
    mapping_blob = json.dumps(mapping, indent=2)
    claims_blob = json.dumps(claims, indent=2)

    user = MAPPING_USER_TEMPLATE.format(
        paper_id=paper_id,
        mapping_blob=mapping_blob,
        claims_blob=claims_blob,
        lean_snip=lean_snip,
    )

    messages = [
        LLMMessage(role="system", content=MAPPING_SYSTEM),
        LLMMessage(role="user", content=user),
    ]
    t0 = time.perf_counter()
    resp = provider.complete(messages, model=model, temperature=temperature, max_tokens=2048)
    latency = time.perf_counter() - t0
    data = extract_json_object(resp.text)
    data.setdefault("paper_id", paper_id)
    data["schema_version"] = "0.1.0"
    data["verification_boundary"] = "human_review_only"
    data.setdefault("proposals", [])
    meta_out = {
        "provider": "prime_intellect",
        "model": resp.model,
        "model_version": "unknown",
        "created_at": datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "latency_seconds": round(latency, 3),
        "prompt_tokens": resp.prompt_tokens,
        "completion_tokens": resp.completion_tokens,
        "total_tokens": resp.total_tokens,
        "prompt_template_id": MAPPING_PROMPT_TEMPLATE_ID,
        "prompt_template_sha256": mapping_prompt_template_sha256(),
        "input_artifact_sha256": {
            "mapping_json": sha256_hex(mapping_blob),
            "claims_json": sha256_hex(claims_blob),
            "lean_excerpt": sha256_hex(lean_snip),
        },
    }
    existing_meta = data.get("metadata")
    if isinstance(existing_meta, dict):
        merged = {**meta_out, **existing_meta}
        if not merged.get("model_version"):
            merged["model_version"] = "unknown"
        data["metadata"] = merged
    else:
        data["metadata"] = meta_out
    bundle = LlmMappingProposalsBundle.model_validate(data)
    return bundle.model_dump(mode="json", exclude_none=True)
