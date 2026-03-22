"""Validate all corpus and schema artifacts against canonical JSON Schemas."""

import json
from pathlib import Path

from jsonschema import Draft202012Validator
from referencing import Registry, Resource
from referencing.jsonschema import DRAFT202012

from sm_pipeline.validate.kernel_witness import validate_kernel_witness_policy
from sm_pipeline.validate.kernel_contracts_v1 import (
    validate_kernel_contracts_v1,
)

SCHEMA_DIR = Path(__file__).resolve().parents[2] / "schemas"

_BASE_URI = "https://scientific-memory.org/schemas/"


def _load_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def _build_registry(repo_root: Path) -> Registry:
    """Build a referencing Registry from schemas directory."""
    schemas_dir = repo_root.resolve() / "schemas"
    common_uri = f"{_BASE_URI}common.schema.json"
    common_schema = _load_json(schemas_dir / "common.schema.json")
    return Registry().with_resource(
        common_uri,
        Resource.from_contents(common_schema, default_specification=DRAFT202012),
    )


def validate_json_schemas_and_kernels(repo_root: Path) -> None:
    """Gate: validate all corpus objects + `kernels.json` and kernel policies."""
    repo_root = repo_root.resolve()
    schemas_dir = repo_root / "schemas"
    papers_dir = repo_root / "corpus" / "papers"
    registry = _build_registry(repo_root)

    paper_schema = _load_json(schemas_dir / "paper.schema.json")
    claim_schema = _load_json(schemas_dir / "claim.schema.json")
    assumption_schema = _load_json(schemas_dir / "assumption.schema.json")
    symbol_schema = _load_json(schemas_dir / "symbol.schema.json")
    mapping_schema = _load_json(schemas_dir / "mapping.schema.json")
    manifest_schema = _load_json(schemas_dir / "artifact_manifest.schema.json")
    theorem_card_schema = _load_json(schemas_dir / "theorem_card.schema.json")
    kernel_schema = _load_json(schemas_dir / "executable_kernel.schema.json")

    paper_validator = Draft202012Validator(paper_schema, registry=registry)
    claim_validator = Draft202012Validator(claim_schema, registry=registry)
    assumption_validator = Draft202012Validator(assumption_schema, registry=registry)
    symbol_validator = Draft202012Validator(symbol_schema, registry=registry)
    mapping_validator = Draft202012Validator(mapping_schema, registry=registry)
    manifest_validator = Draft202012Validator(manifest_schema, registry=registry)
    theorem_card_validator = Draft202012Validator(theorem_card_schema, registry=registry)
    kernel_validator = Draft202012Validator(kernel_schema, registry=registry)

    for paper_dir in sorted(papers_dir.iterdir()):
        if not paper_dir.is_dir():
            continue
        metadata_path = paper_dir / "metadata.json"
        if not metadata_path.exists():
            continue

        metadata = _load_json(metadata_path)
        paper_validator.validate(metadata)

        claims_path = paper_dir / "claims.json"
        claims = _load_json(claims_path)
        claim_validator.validate(claims)

        assumptions_path = paper_dir / "assumptions.json"
        if assumptions_path.exists():
            assumptions = _load_json(assumptions_path)
            assumption_validator.validate(assumptions)

        symbols_path = paper_dir / "symbols.json"
        if symbols_path.exists():
            symbols = _load_json(symbols_path)
            symbol_validator.validate(symbols)

        mapping_path = paper_dir / "mapping.json"
        if mapping_path.exists():
            mapping = _load_json(mapping_path)
            mapping_validator.validate(mapping)

        manifest_path = paper_dir / "manifest.json"
        if manifest_path.exists():
            manifest = _load_json(manifest_path)
            manifest_validator.validate(manifest)

        cards_path = paper_dir / "theorem_cards.json"
        if cards_path.exists():
            cards = _load_json(cards_path)
            theorem_card_validator.validate(cards)

    kernels_path = repo_root / "corpus" / "kernels.json"
    if kernels_path.exists():
        raw = kernels_path.read_text(encoding="utf-8").strip()
        if raw:
            kernels = json.loads(raw)
            if isinstance(kernels, list):
                kernel_validator.validate(kernels)
                validate_kernel_witness_policy(repo_root)
                validate_kernel_contracts_v1(repo_root)


def validate_repo(repo_root: Path) -> None:
    """Validate corpus and run all integrity gates (gate engine wrapper)."""
    from sm_pipeline.validate.gate_engine import run_all_gates

    run_all_gates(repo_root)
