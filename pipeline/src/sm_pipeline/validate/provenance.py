"""Provenance validation (Gate 3).

Every claim has source_span; no dangling declarations.
"""

import json
from pathlib import Path


class ProvenanceError(Exception):
    """Raised when provenance integrity check fails."""

    pass


def _is_stress_scaffold(metadata: object, claims: object) -> bool:
    """Allow limited sentinel-sha manifests for hard-dimension scaffolds."""
    if not isinstance(metadata, dict):
        return False
    tags = metadata.get("tags")
    if not isinstance(tags, list):
        return False
    has_hardness_tag = any(isinstance(t, str) and t.startswith("hardness.primary:") for t in tags)
    if not has_hardness_tag:
        return False
    # Keep exception narrow: only empty-claim intake scaffolds may keep manifests.
    return isinstance(claims, list) and len(claims) == 0


def validate_provenance(repo_root: Path) -> None:
    """
    Enforce SPEC Gate 3:
    - Every claim has source_span.
    - Every declaration in manifest.declaration_index is tied to a claim
      via mapping.claim_to_decl.
    """
    repo_root = repo_root.resolve()
    papers_dir = repo_root / "corpus" / "papers"
    if not papers_dir.is_dir():
        return

    ZERO_SENTINEL = "0" * 64

    for paper_dir in sorted(papers_dir.iterdir()):
        if not paper_dir.is_dir():
            continue
        metadata_path = paper_dir / "metadata.json"
        if not metadata_path.exists():
            continue
        metadata = _load_json(metadata_path)
        claims_path = paper_dir / "claims.json"
        claims = _load_json(claims_path) if claims_path.exists() else []
        has_manifest = (paper_dir / "manifest.json").exists()
        if isinstance(metadata, dict) and has_manifest:
            source = metadata.get("source")
            if isinstance(source, dict):
                sha = (source.get("sha256") or "").strip()
                if sha == ZERO_SENTINEL:
                    if not _is_stress_scaffold(metadata, claims):
                        raise ProvenanceError(
                            f"Paper {paper_dir.name} has manifest but source.sha256 is the "
                            "all-zero sentinel; run hash-source or add real source file"
                        )

        if not claims_path.exists():
            continue
        if not isinstance(claims, list):
            continue
        for claim in claims:
            if not isinstance(claim, dict):
                continue
            if not claim.get("source_span"):
                raise ProvenanceError(
                    f"Claim {claim.get('id', '?')} in {paper_dir.name} missing source_span"
                )

        manifest_path = paper_dir / "manifest.json"
        mapping_path = paper_dir / "mapping.json"
        if not manifest_path.exists():
            continue
        manifest = _load_json(manifest_path)
        if not isinstance(manifest, dict):
            continue
        decl_index = manifest.get("declaration_index")
        if not isinstance(decl_index, list) or len(decl_index) == 0:
            continue

        if not mapping_path.exists():
            raise ProvenanceError(
                f"Paper {paper_dir.name} has declaration_index but no mapping.json"
            )
        mapping = _load_json(mapping_path)
        if not isinstance(mapping, dict):
            raise ProvenanceError(f"Paper {paper_dir.name} mapping.json invalid")
        namespace = (mapping.get("namespace") or "").strip()
        claim_to_decl = mapping.get("claim_to_decl")
        if not isinstance(claim_to_decl, dict):
            claim_to_decl = {}
        declared_from_claims = set()
        for _cid, short_decl in claim_to_decl.items():
            if namespace:
                declared_from_claims.add(f"{namespace}.{short_decl}")
            else:
                declared_from_claims.add(str(short_decl))

        for decl in decl_index:
            if decl not in declared_from_claims:
                raise ProvenanceError(
                    f"Paper {paper_dir.name}: declaration {decl} in declaration_index "
                    "has no originating claim in mapping.claim_to_decl"
                )


def _load_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))
