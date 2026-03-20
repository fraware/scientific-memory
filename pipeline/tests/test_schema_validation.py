import hashlib
import json
import shutil
import tempfile
from pathlib import Path

from jsonschema import Draft202012Validator
from referencing import Registry, Resource
from referencing.jsonschema import DRAFT202012

from sm_pipeline.validate.schemas import validate_repo


def _load_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def test_pinned_fixture_checksum() -> None:
    """Pinned fixture content hash must match .checksum (SPEC 10.5)."""
    repo_root = Path(__file__).resolve().parents[2]
    fixture_dir = repo_root / "pipeline" / "tests" / "fixtures" / "corpus_paper"
    files = sorted(fixture_dir.glob("*.json"))
    h = hashlib.sha256()
    for f in files:
        h.update(json.dumps(json.loads(f.read_text(encoding="utf-8")), sort_keys=True).encode())
    checksum_path = fixture_dir / ".checksum"
    expected = checksum_path.read_text(encoding="utf-8").strip()
    assert h.hexdigest() == expected, (
        "Pinned fixture changed; update .checksum or revert. See pipeline/tests/fixtures/corpus_paper/PINNED.md"
    )


def test_validate_repo_on_pinned_fixture() -> None:
    """validate_repo passes on the pinned fixture corpus (full schema validation)."""
    repo_root = Path(__file__).resolve().parents[2]
    fixture_dir = repo_root / "pipeline" / "tests" / "fixtures" / "corpus_paper"
    tmp = Path(tempfile.mkdtemp())
    try:
        (tmp / "schemas").mkdir(parents=True)
        for f in (repo_root / "schemas").glob("*.json"):
            shutil.copy(f, tmp / "schemas" / f.name)
        (tmp / "corpus" / "papers" / "pinned_fixture").mkdir(parents=True)
        for f in fixture_dir.glob("*.json"):
            shutil.copy(f, tmp / "corpus" / "papers" / "pinned_fixture" / f.name)
        (tmp / "docs").mkdir(parents=True)
        (tmp / "docs" / "contributor-playbook.md").write_text(
            "# Contributor playbook\n\n## Migration notes\n\n- **2026-03**: Example entry for fixture.\n",
            encoding="utf-8",
        )
        paper_dir = tmp / "corpus" / "papers" / "pinned_fixture"
        paper_dir.mkdir(parents=True, exist_ok=True)
        (paper_dir / "extraction_run.json").write_text(
            json.dumps(
                {"paper_id": "pinned_fixture", "recorded_at": "2026-03-01T00:00:00Z", "claim_count": 1, "claims_with_source_span": 0, "assumption_count": 0},
                indent=2,
            ),
            encoding="utf-8",
        )
        validate_repo(tmp)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_validate_repo_schemas() -> None:
    """Schema validation passes for corpus fixture."""
    repo_root = Path(__file__).resolve().parents[2]
    schemas_dir = repo_root / "schemas"
    papers_dir = repo_root / "corpus" / "papers"

    common = _load_json(schemas_dir / "common.schema.json")
    paper_schema = _load_json(schemas_dir / "paper.schema.json")
    claim_schema = _load_json(schemas_dir / "claim.schema.json")
    
    # Build registry with common schema for $ref resolution
    base_uri = "https://scientific-memory.org/schemas/"
    common_uri = f"{base_uri}common.schema.json"
    registry = Registry().with_resource(
        common_uri, Resource.from_contents(common, default_specification=DRAFT202012)
    )
    
    paper_validator = Draft202012Validator(paper_schema, registry=registry)
    claim_validator = Draft202012Validator(claim_schema, registry=registry)

    for paper_dir in sorted(papers_dir.iterdir()):
        if not paper_dir.is_dir():
            continue
        metadata_path = paper_dir / "metadata.json"
        if not metadata_path.exists():
            continue
        metadata = _load_json(metadata_path)
        paper_validator.validate(metadata)
        claims = _load_json(paper_dir / "claims.json")
        claim_validator.validate(claims)


def test_metadata_conforms_to_paper_schema() -> None:
    """Single fixture metadata validates against paper schema."""
    repo_root = Path(__file__).resolve().parents[2]
    metadata = _load_json(
        repo_root / "corpus" / "papers" / "langmuir_1918_adsorption" / "metadata.json"
    )
    paper_schema = _load_json(repo_root / "schemas" / "paper.schema.json")
    common = _load_json(repo_root / "schemas" / "common.schema.json")
    
    # Build registry with common schema for $ref resolution
    base_uri = "https://scientific-memory.org/schemas/"
    common_uri = f"{base_uri}common.schema.json"
    registry = Registry().with_resource(
        common_uri, Resource.from_contents(common, default_specification=DRAFT202012)
    )
    
    paper_validator = Draft202012Validator(paper_schema, registry=registry)
    paper_validator.validate(metadata)
