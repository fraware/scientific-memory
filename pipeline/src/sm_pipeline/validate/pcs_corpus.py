"""Validate imported PCS claims under corpus/pcs/claims/."""

from __future__ import annotations

import json
from pathlib import Path

from sm_pipeline.pcs_import.bundle_utils import bundle_for_validation
from sm_pipeline.pcs_import.science_claim_bundle_importer import load_read_model
from sm_pipeline.pcs_validate.validator import BundleValidationError, validate_signed_bundle

REQUIRED_READ_MODEL_KEYS = frozenset(
    {
        "claim",
        "assumption_set",
        "runtime_receipt",
        "trace_certificate",
        "verification_result",
        "artifact_hashes",
        "canonical_digests",
        "source_repositories",
        "reproduce_commands",
        "verify_commands",
        "limitations",
        "limitation_notice",
    }
)

IMPORT_REPORT_KEYS = frozenset(
    {
        "claim_id",
        "imported_at",
        "source_bundle_path",
        "verification_status",
        "warnings",
        "stale_artifacts",
        "render_path",
    }
)


def validate_pcs_corpus(repo_root: Path) -> None:
    """Re-validate signed bundles and check read models for all imported PCS claims."""
    repo_root = repo_root.resolve()
    claims_root = repo_root / "corpus" / "pcs" / "claims"
    if not claims_root.is_dir():
        return

    errors: list[str] = []
    for claim_dir in sorted(claims_root.iterdir()):
        if not claim_dir.is_dir():
            continue
        claim_id = claim_dir.name
        signed_path = claim_dir / "signed_bundle.json"
        if not signed_path.is_file():
            errors.append(f"{claim_id}: missing signed_bundle.json")
            continue

        bundle = json.loads(signed_path.read_text(encoding="utf-8"))
        if not isinstance(bundle, dict):
            errors.append(f"{claim_id}: signed_bundle.json must be an object")
            continue

        try:
            validate_signed_bundle(
                bundle_for_validation(bundle), repo_root=repo_root, strict=True
            )
        except BundleValidationError as exc:
            errors.append(f"{claim_id}: bundle validation failed: {exc}")

        read_model = load_read_model(repo_root, claim_id)
        if read_model is None:
            errors.append(f"{claim_id}: missing read_model.json")
            continue

        missing = REQUIRED_READ_MODEL_KEYS - set(read_model.keys())
        if missing:
            errors.append(f"{claim_id}: read_model missing keys: {sorted(missing)}")

        report_path = claim_dir / "scientific_memory_import_report.json"
        if not report_path.is_file():
            errors.append(f"{claim_id}: missing scientific_memory_import_report.json")
        else:
            report = json.loads(report_path.read_text(encoding="utf-8"))
            if not isinstance(report, dict):
                errors.append(f"{claim_id}: import report must be an object")
            else:
                missing_report = IMPORT_REPORT_KEYS - set(report.keys())
                if missing_report:
                    errors.append(
                        f"{claim_id}: import report missing keys: {sorted(missing_report)}"
                    )

    if errors:
        raise ValueError("PCS corpus validation failed:\n" + "\n".join(errors))
