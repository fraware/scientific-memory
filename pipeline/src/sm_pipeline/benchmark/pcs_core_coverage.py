"""PCS-core explain_quality_section_id coverage for rendering benchmarks."""

from __future__ import annotations

from typing import Any

from sm_pipeline.benchmark.pcs_sections import evaluate_section_coverage, section_present
from sm_pipeline.pcs_validate.canonical_hash import canonical_hash

# pcs-core explain_quality_section_id enum (ExplainQualityReport.v0).
EXPLAIN_QUALITY_SECTION_IDS: tuple[str, ...] = (
    "provenance",
    "hashes",
    "handoffs",
    "verification",
    "formal_checks",
    "limitations",
    "lineage",
    "repair_hints",
)

SOURCE_REPO = "https://github.com/fraware/scientific-memory"

# Map interpretability section labels to pcs-core explain-quality sections.
INTERPRETABILITY_TO_EXPLAIN_QUALITY: dict[str, str] = {
    "Claim": "provenance",
    "Workflow Profile": "provenance",
    "Runtime Evidence": "provenance",
    "Release Manifest": "provenance",
    "Release Chain Validation": "verification",
    "Artifact Registry": "provenance",
    "Artifact Dependency Graph": "provenance",
    "Source Repositories": "provenance",
    "Reproduce / Verify": "provenance",
    "Artifact Hashes": "hashes",
    "Handoff Manifests": "handoffs",
    "Certificate or Witness": "verification",
    "Verification Result": "verification",
    "Formal Trust Kernel": "formal_checks",
    "Limitations": "limitations",
    "Lineage": "lineage",
    "Staleness": "repair_hints",
}


def build_explain_quality_report(
    *,
    case_id: str,
    claim_id: str,
    read_model: dict[str, Any],
    section_coverage: dict[str, Any] | None = None,
    suite_id: str,
    source_commit: str,
) -> dict[str, Any]:
    """Build ExplainQualityReport.v0-shaped coverage for one benchmark case."""
    coverage = section_coverage or evaluate_section_coverage(read_model)
    present_labels = set(coverage.get("present_sections") or [])

    sections: list[dict[str, Any]] = []
    for eq_id in EXPLAIN_QUALITY_SECTION_IDS:
        interp_labels = [label for label, mapped in INTERPRETABILITY_TO_EXPLAIN_QUALITY.items() if mapped == eq_id]
        rendered_labels = [label for label in interp_labels if label in present_labels]
        rendered = bool(rendered_labels) or _explain_quality_present(read_model, eq_id)
        sections.append(
            {
                "explain_quality_section_id": eq_id,
                "rendered": rendered,
                "interpretability_sections": rendered_labels,
            },
        )

    present_count = sum(1 for row in sections if row.get("rendered"))
    required_count = len(EXPLAIN_QUALITY_SECTION_IDS)
    report: dict[str, Any] = {
        "schema_version": "v0",
        "report_id": f"explain-quality-{case_id}",
        "suite_id": suite_id,
        "case_id": case_id,
        "claim_id": claim_id,
        "producer_id": "scientific-memory",
        "required_sections": list(EXPLAIN_QUALITY_SECTION_IDS),
        "sections": sections,
        "sections_present_count": present_count,
        "sections_required_count": required_count,
        "quality_score": round(present_count / required_count, 4) if required_count else 1.0,
        "gaps": [row["explain_quality_section_id"] for row in sections if not row.get("rendered")],
        "source_repo": SOURCE_REPO,
        "source_commit": source_commit,
    }
    report["signature_or_digest"] = canonical_hash(report)
    return report


def _explain_quality_present(read_model: dict[str, Any], eq_id: str) -> bool:
    if eq_id == "repair_hints":
        staleness = read_model.get("staleness") if isinstance(read_model.get("staleness"), dict) else {}
        lineage = read_model.get("lineage") if isinstance(read_model.get("lineage"), dict) else {}
        return bool(staleness.get("repair_hint") or lineage.get("recommended_action"))
    if eq_id == "formal_checks":
        kernel = read_model.get("formal_trust_kernel")
        return isinstance(kernel, dict) and bool(kernel.get("lean_check_results"))
    if eq_id == "handoffs":
        handoffs = read_model.get("handoff_manifests")
        return isinstance(handoffs, list) and len(handoffs) > 0
    if eq_id == "hashes":
        hashes = read_model.get("artifact_hashes")
        return isinstance(hashes, (list, dict)) and len(hashes) > 0
    if eq_id == "lineage":
        lineage = read_model.get("lineage")
        return isinstance(lineage, dict) and bool(lineage.get("claim_id"))
    if eq_id == "limitations":
        return bool(read_model.get("limitations") or read_model.get("limitation_notice"))
    if eq_id == "verification":
        return section_present(read_model, "Verification Result") or section_present(
            read_model,
            "Certificate or Witness",
        )
    if eq_id == "provenance":
        return section_present(read_model, "Claim") or section_present(read_model, "Release Manifest")
    return False


def suite_id_for_cases_path(cases_path: str | None) -> str:
    name = (cases_path or "").replace("\\", "/").rstrip("/").split("/")[-1]
    if name == "external_reviewer_minimal":
        return "scientific-memory-external-reviewer-v0"
    return "scientific-memory-rendering-v0"
