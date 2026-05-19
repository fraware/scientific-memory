"""Validate ProofObligation.v0 and LeanCheckResult.v0 for strict release import."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from sm_pipeline.pcs_import.formal_trust_protocol import (
    LEAN_CHECK_RESULT_FILENAMES,
    PROOF_OBLIGATION_FILENAMES,
    workflow_requires_formal_trust,
)
from sm_pipeline.pcs_validate.canonical_hash import canonical_hash
from sm_pipeline.pcs_validate.validator import BundleValidationError, validator_for

PROOF_CHECKED = "ProofChecked"


def _repo_root(repo_root: Path | None) -> Path:
    if repo_root is not None:
        return repo_root.resolve()
    return Path(__file__).resolve().parents[4]


def _load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(data, dict):
        raise BundleValidationError(f"{path.name}: root must be a JSON object")
    return data


def _resolve_artifact(release_dir: Path, names: tuple[str, ...]) -> Path | None:
    for name in names:
        path = release_dir / name
        if path.is_file():
            return path
    return None


def _validate_schema(data: dict[str, Any], schema_name: str, repo_root: Path) -> None:
    validator = validator_for(schema_name, repo_root)
    errors = sorted(validator.iter_errors(data), key=lambda item: item.path)
    if errors:
        raise BundleValidationError(
            f"{schema_name}: " + "; ".join(err.message for err in errors[:5]),
        )


def _obligation_ids(obligations: list[dict[str, Any]]) -> set[str]:
    return {
        str(item["obligation_id"])
        for item in obligations
        if isinstance(item, dict) and item.get("obligation_id")
    }


def require_formal_trust_artifacts(
    release_dir: Path,
    manifest: dict[str, Any],
    *,
    repo_root: Path | None = None,
    workflow_profile: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Load and validate formal trust artifacts when required by workflow profile."""
    root = _repo_root(repo_root)
    workflow_profile_id = str(manifest.get("workflow_profile_id") or "")
    if not workflow_requires_formal_trust(
        workflow_profile,
        workflow_profile_id=workflow_profile_id,
        repo_root=root,
    ):
        return {}, {}
    release_dir = release_dir.resolve()
    release_id = str(manifest.get("release_id") or "")

    obligation_path = _resolve_artifact(release_dir, PROOF_OBLIGATION_FILENAMES)
    if obligation_path is None:
        raise BundleValidationError(
            "missing ProofObligation.v0 (proof_obligation.v0.json) required for formal trust workflow",
        )

    lean_path = _resolve_artifact(release_dir, LEAN_CHECK_RESULT_FILENAMES)
    if lean_path is None:
        raise BundleValidationError(
            "missing LeanCheckResult.v0 (lean_check_result.v0.json) required for formal trust workflow",
        )

    obligation = _load_json(obligation_path)
    lean = _load_json(lean_path)
    _validate_schema(obligation, "ProofObligation.v0.schema.json", root)
    _validate_schema(lean, "LeanCheckResult.v0.schema.json", root)

    if obligation.get("signature_or_digest") != canonical_hash(obligation):
        raise BundleValidationError("ProofObligation.v0: signature_or_digest mismatch")
    if lean.get("signature_or_digest") != canonical_hash(lean):
        raise BundleValidationError("LeanCheckResult.v0: signature_or_digest mismatch")

    if release_id and obligation.get("release_id") != release_id:
        raise BundleValidationError(
            f"ProofObligation release_id {obligation.get('release_id')!r} != manifest {release_id!r}",
        )
    if release_id and lean.get("release_id") != release_id:
        raise BundleValidationError(
            f"LeanCheckResult release_id {lean.get('release_id')!r} != manifest {release_id!r}",
        )

    obligation_set_id = str(obligation.get("obligation_set_id") or "")
    if obligation_set_id and lean.get("obligation_set_id") != obligation_set_id:
        raise BundleValidationError(
            "LeanCheckResult obligation_set_id does not match ProofObligation obligation_set_id",
        )

    if lean.get("status") != PROOF_CHECKED:
        raise BundleValidationError(
            f"LeanCheckResult status must be {PROOF_CHECKED}, got {lean.get('status')!r}",
        )

    obligations = obligation.get("obligations")
    if not isinstance(obligations, list) or not obligations:
        raise BundleValidationError("ProofObligation.v0: obligations must be a non-empty array")

    expected_ids = _obligation_ids([item for item in obligations if isinstance(item, dict)])
    results = lean.get("results")
    if not isinstance(results, list) or not results:
        raise BundleValidationError("LeanCheckResult.v0: results must be a non-empty array")

    result_ids = _obligation_ids([item for item in results if isinstance(item, dict)])
    if result_ids != expected_ids:
        missing = expected_ids - result_ids
        extra = result_ids - expected_ids
        parts: list[str] = []
        if missing:
            parts.append(f"missing results for {sorted(missing)}")
        if extra:
            parts.append(f"unexpected results for {sorted(extra)}")
        raise BundleValidationError("LeanCheckResult obligation mismatch: " + "; ".join(parts))

    for entry in results:
        if not isinstance(entry, dict):
            continue
        if entry.get("result") == "failed" or entry.get("status") == "Rejected":
            raise BundleValidationError(
                f"LeanCheckResult contains failed obligation {entry.get('obligation_id')!r}",
            )

    return obligation, lean
