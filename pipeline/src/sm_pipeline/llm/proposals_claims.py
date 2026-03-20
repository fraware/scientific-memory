"""Generate llm_claim_proposals.json via Prime Intellect (suggest-only)."""

from __future__ import annotations

import json
import time
from datetime import UTC, datetime
from pathlib import Path

from sm_pipeline.llm.json_extract import extract_json_object
from sm_pipeline.llm.prompt_templates import (
    CLAIM_PROMPT_TEMPLATE_ID,
    CLAIM_SYSTEM,
    CLAIM_USER_TEMPLATE,
    claim_prompt_template_sha256,
    sha256_hex,
)
from sm_pipeline.llm.provider import LLMMessage, LLMProvider
from sm_pipeline.llm.source_context import gather_paper_source_text, load_json_if_exists
from sm_pipeline.models.llm_proposals import LlmClaimProposalsBundle


def generate_llm_claim_proposals(
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

    meta = load_json_if_exists(paper_dir / "metadata.json")
    meta_blob = json.dumps(meta, indent=2) if meta is not None else "{}"
    existing_claims = load_json_if_exists(paper_dir / "claims.json")
    claims_blob = json.dumps(existing_claims, indent=2) if existing_claims is not None else "[]"
    suggested = load_json_if_exists(paper_dir / "suggested_claims.json")
    suggested_blob = json.dumps(suggested, indent=2) if suggested is not None else "null"
    source_text = gather_paper_source_text(paper_dir)
    source_section = source_text if source_text else "(no text files collected)"

    user = CLAIM_USER_TEMPLATE.format(
        paper_id=paper_id,
        meta_blob=meta_blob,
        claims_blob=claims_blob,
        suggested_blob=suggested_blob,
        source_section=source_section,
    )

    messages = [
        LLMMessage(role="system", content=CLAIM_SYSTEM),
        LLMMessage(role="user", content=user),
    ]
    t0 = time.perf_counter()
    resp = provider.complete(messages, model=model, temperature=temperature, max_tokens=4096)
    latency = time.perf_counter() - t0
    data = extract_json_object(resp.text)
    data.setdefault("paper_id", paper_id)
    data["schema_version"] = "0.1.0"
    data["verification_boundary"] = "human_review_only"
    data.setdefault("proposals", [])
    meta_out = {
        "provider": "prime_intellect",
        "model": resp.model,
        "created_at": datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "latency_seconds": round(latency, 3),
        "prompt_tokens": resp.prompt_tokens,
        "completion_tokens": resp.completion_tokens,
        "total_tokens": resp.total_tokens,
        "prompt_template_id": CLAIM_PROMPT_TEMPLATE_ID,
        "prompt_template_sha256": claim_prompt_template_sha256(),
        "input_artifact_sha256": {
            "metadata_json": sha256_hex(meta_blob),
            "claims_json": sha256_hex(claims_blob),
            "suggested_claims_json": sha256_hex(suggested_blob),
            "source_text": sha256_hex(source_section),
        },
    }
    existing_meta = data.get("metadata")
    if isinstance(existing_meta, dict):
        merged = {**meta_out, **existing_meta}
        data["metadata"] = merged
    else:
        data["metadata"] = meta_out
    bundle = LlmClaimProposalsBundle.model_validate(data)
    return bundle.model_dump(mode="json")
