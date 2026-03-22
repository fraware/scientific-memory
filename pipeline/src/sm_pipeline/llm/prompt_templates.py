"""Versioned LLM prompt templates: IDs and SHA-256 for reproducible runs and benchmark reports."""

from __future__ import annotations

import hashlib
from typing import Final


def sha256_hex(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


CLAIM_PROMPT_TEMPLATE_ID: Final = "llm_claim_proposals/v1"

CLAIM_SYSTEM: Final = """You are assisting with the Scientific Memory corpus. Output MUST be a single JSON object only (no markdown prose outside JSON).

The JSON must match this shape:
{
  "paper_id": "<same as given>",
  "schema_version": "0.1.0",
  "verification_boundary": "human_review_only",
  "proposals": [
    {
      "claim": { ... full claim object ... },
      "rationale": "string",
      "confidence": 0.0,
      "evidence_quote": "short excerpt from source supporting source_span"
    }
  ]
}

Each "claim" must be a valid Scientific Memory claim object with fields:
id, paper_id, section, source_span (source_file, start/end with page>=1 and offset>=0),
informal_text (non-empty), claim_type (one of: definition, theorem, lemma, proposition, corollary, estimator, identity, conservation_law, control_rule, dimensional_constraint, algorithmic_step, acceptance_criterion, editorial_exposition),
status (one of: unparsed, parsed, mapped, stubbed, compiles_with_sorries, machine_checked, linked_to_kernel, disputed, superseded),
linked_symbols (array of ids), linked_assumptions (array of ids), linked_formal_targets (array of strings, may be empty).

Use source_span that honestly reflects where the claim is supported in the provided source text (page/offset are logical offsets if only one file; use page=1 and increasing offsets if unsure).

Proposals are suggestions only; a human will review before merge. Prefer precision over quantity."""

CLAIM_USER_TEMPLATE: Final = """paper_id: {paper_id}

metadata.json:
{meta_blob}

current claims.json (may be empty):
{claims_blob}

suggested_claims.json from pandoc (may be null):
{suggested_blob}

source text under corpus/papers/{paper_id}/source/ (may be empty):
{source_section}

Task: propose new or revised claims as JSON per system instructions. If source is empty, return proposals: [] (still valid JSON)."""


def claim_prompt_template_sha256() -> str:
    return sha256_hex(f"{CLAIM_SYSTEM}\n---SM_USER_TEMPLATE---\n{CLAIM_USER_TEMPLATE}")


MAPPING_PROMPT_TEMPLATE_ID: Final = "llm_mapping_proposals/v1"

_MAPPING_SYSTEM: Final = """You assist the Scientific Memory project with claim-to-Lean mapping suggestions.

Output a single JSON object only (no markdown outside JSON) with this shape:
{
  "paper_id": "<given>",
  "schema_version": "0.1.0",
  "verification_boundary": "human_review_only",
  "proposals": [
    {
      "claim_id": "existing_claim_id",
      "lean_declaration_short_name": "snake_case_or_lowerCamel",
      "rationale": "why this name fits",
      "confidence": 0.0
    }
  ]
}

lean_declaration_short_name must be a valid Lean declaration name segment (letters, digits, underscore; may end with prime ').

Only propose mappings for claims that should link to formal code; omit uncertain ones. Suggestions are reviewed by humans."""

MAPPING_SYSTEM: Final = _MAPPING_SYSTEM

MAPPING_USER_TEMPLATE: Final = """paper_id: {paper_id}

mapping.json:
{mapping_blob}

claims.json (subset for mapping):
{claims_blob}

Lean file excerpt (may be truncated):
{lean_snip}

Task: propose claim_id -> lean_declaration_short_name entries as JSON per system instructions."""


def mapping_prompt_template_sha256() -> str:
    return sha256_hex(f"{MAPPING_SYSTEM}\n---SM_USER_TEMPLATE---\n{MAPPING_USER_TEMPLATE}")


LEAN_PROMPT_TEMPLATE_ID: Final = "llm_lean_proposals/v1"

_LEAN_SYSTEM: Final = """You assist Scientific Memory contributors who are not Lean experts.

Output a single JSON object only (no markdown outside JSON) with this shape:
{
  "paper_id": "<given>",
  "schema_version": "0.1.0",
  "verification_boundary": "human_review_only",
  "proposals": [
    {
      "proposal_id": "unique_string_id",
      "paper_id": "<given>",
      "claim_id": "optional_existing_claim_id",
      "target_file": "formal/ScientificMemory/.../File.lean",
      "target_decl": "short_declaration_name_or_hint",
      "edit_kind": "new_theorem" | "proof_repair" | "lemma_extraction",
      "replacements": [ { "find": "exact_unique_snippet_from_file", "replace": "new_text" } ],
      "patch_text": "optional human-readable draft (not applied automatically)",
      "rationale": "string",
      "confidence": 0.0,
      "safety_flags": ["optional flags e.g. needs_import"]
    }
  ]
}

Rules:
- target_file MUST be repo-relative and start with formal/ (no ..).
- replacements: each "find" must be a UNIQUE substring in the target Lean file (exactly one match) so a human can run find/replace apply safely.
- Prefer small surgical edits over rewriting whole files.
- If you cannot identify a safe unique find string, return proposals: [] (still valid JSON).
- Never invent claim_ids that are not in the provided claims list.
- Suggestions are reviewed by humans; nothing is applied automatically."""

LEAN_SYSTEM: Final = _LEAN_SYSTEM

LEAN_USER_TEMPLATE: Final = """paper_id: {paper_id}
{focus_section}mapping.json:
{mapping_blob}

claims.json:
{claims_blob}

theorem_cards.json (may be null):
{cards_blob}

Lean file excerpt (truncated):
{lean_snip}

Task: propose surgical Lean edits as JSON per system instructions."""


def lean_prompt_template_sha256() -> str:
    return sha256_hex(f"{LEAN_SYSTEM}\n---SM_USER_TEMPLATE---\n{LEAN_USER_TEMPLATE}")


def declared_llm_prompt_template_versions() -> dict[str, str]:
    """Template id -> SHA-256 of system+user template literals (for benchmark reports)."""
    return {
        CLAIM_PROMPT_TEMPLATE_ID: claim_prompt_template_sha256(),
        MAPPING_PROMPT_TEMPLATE_ID: mapping_prompt_template_sha256(),
        LEAN_PROMPT_TEMPLATE_ID: lean_prompt_template_sha256(),
    }
