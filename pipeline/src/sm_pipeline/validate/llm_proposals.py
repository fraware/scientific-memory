"""Non-blocking validation for optional LLM proposal sidecar files."""

from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator
from referencing import Registry, Resource
from referencing.jsonschema import DRAFT202012

_BASE_URI = "https://scientific-memory.org/schemas/"


def _load(repo_root: Path, name: str) -> object:
    return json.loads((repo_root / "schemas" / name).read_text(encoding="utf-8"))


def _registry_for_llm(repo_root: Path) -> Registry:
    """Registry with common + claim + both LLM proposal schemas (for nested $ref)."""
    repo_root = repo_root.resolve()
    reg: Registry = Registry()
    for fname in (
        "common.schema.json",
        "claim.schema.json",
        "assumption.schema.json",
        "symbol.schema.json",
        "llm_run_provenance.schema.json",
        "llm_claim_proposals.schema.json",
        "llm_mapping_proposals.schema.json",
        "llm_lean_proposals.schema.json",
        "suggested_assumptions.schema.json",
        "suggested_symbols.schema.json",
        "suggested_mapping.schema.json",
    ):
        uri = f"{_BASE_URI}{fname}"
        schema = _load(repo_root, fname)
        reg = reg.with_resource(
            uri, Resource.from_contents(schema, default_specification=DRAFT202012)
        )
    return reg


def validate_llm_proposal_sidecars_warn(repo_root: Path) -> list[str]:
    """Return human-readable warnings for invalid sidecars (does not raise)."""
    repo_root = repo_root.resolve()
    papers_dir = repo_root / "corpus" / "papers"
    if not papers_dir.is_dir():
        return []
    reg = _registry_for_llm(repo_root)
    validators: dict[str, tuple[str, Draft202012Validator]] = {
        "llm_claim_proposals.json": (
            "llm_claim_proposals.schema.json",
            Draft202012Validator(_load(repo_root, "llm_claim_proposals.schema.json"), registry=reg),
        ),
        "llm_mapping_proposals.json": (
            "llm_mapping_proposals.schema.json",
            Draft202012Validator(
                _load(repo_root, "llm_mapping_proposals.schema.json"), registry=reg
            ),
        ),
        "llm_lean_proposals.json": (
            "llm_lean_proposals.schema.json",
            Draft202012Validator(
                _load(repo_root, "llm_lean_proposals.schema.json"), registry=reg
            ),
        ),
        "suggested_assumptions.json": (
            "suggested_assumptions.schema.json",
            Draft202012Validator(
                _load(repo_root, "suggested_assumptions.schema.json"), registry=reg
            ),
        ),
        "suggested_symbols.json": (
            "suggested_symbols.schema.json",
            Draft202012Validator(_load(repo_root, "suggested_symbols.schema.json"), registry=reg),
        ),
        "suggested_mapping.json": (
            "suggested_mapping.schema.json",
            Draft202012Validator(_load(repo_root, "suggested_mapping.schema.json"), registry=reg),
        ),
    }
    warnings: list[str] = []
    for paper_dir in sorted(papers_dir.iterdir()):
        if not paper_dir.is_dir():
            continue
        pid = paper_dir.name
        for filename, (_schema_name, validator) in validators.items():
            path = paper_dir / filename
            if not path.is_file():
                continue
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                validator.validate(data)
            except Exception as e:
                warnings.append(f"{pid}/{filename}: {e}")
    return warnings
