"""PCS read-model section coverage for rendering benchmarks."""

from __future__ import annotations

from typing import Any

# Benchmark contract (pcs-bench / rendering suites) — evidence-interface sections.
BENCHMARK_RENDERING_SECTIONS: tuple[str, ...] = (
    "Claim",
    "Workflow Profile",
    "Runtime Evidence",
    "Certificate or Witness",
    "Verification Result",
    "Formal Trust Kernel",
    "Release Manifest",
    "Release Chain Validation",
    "Artifact Registry",
    "Handoff Manifests",
    "Artifact Dependency Graph",
    "Lineage",
    "Staleness",
    "Artifact Hashes",
    "Source Repositories",
    "Reproduce / Verify",
    "Limitations",
)

# Portal interpretability (includes Assumptions for full human-facing pages).
REQUIRED_INTERPRETABILITY_SECTIONS: tuple[str, ...] = (
    "Claim",
    "Workflow Profile",
    "Assumptions",
    "Runtime Evidence",
    "Certificate or Witness",
    "Verification Result",
    "Formal Trust Kernel",
    "Release Manifest",
    "Release Chain Validation",
    "Artifact Registry",
    "Handoff Manifests",
    "Artifact Dependency Graph",
    "Lineage",
    "Staleness",
    "Artifact Hashes",
    "Source Repositories",
    "Reproduce / Verify",
    "Limitations",
)

_SECTION_CHECKS: dict[str, tuple[str, ...]] = {
    "Claim": ("claim",),
    "Workflow Profile": ("workflow_profile",),
    "Assumptions": ("assumption_set",),
    "Runtime Evidence": ("runtime_receipt",),
    "Certificate or Witness": (
        "trace_certificate",
        "tool_use_certificate",
        "computation_witness",
    ),
    "Verification Result": ("verification_result",),
    "Formal Trust Kernel": ("formal_trust_kernel",),
    "Release Manifest": ("release_manifest",),
    "Release Chain Validation": ("release_chain_validation",),
    "Artifact Registry": ("artifact_registry",),
    "Handoff Manifests": ("handoff_manifests",),
    "Artifact Dependency Graph": ("artifact_dependency_graph",),
    "Lineage": ("lineage",),
    "Staleness": ("staleness",),
    "Artifact Hashes": ("artifact_hashes",),
    "Source Repositories": ("source_repositories",),
    "Reproduce / Verify": ("reproduce_commands", "verify_commands"),
    "Limitations": ("limitations", "limitation_notice"),
}


def _value_present(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, dict)):
        return len(value) > 0
    return True


def section_present(read_model: dict[str, Any], section_label: str) -> bool:
    keys = _SECTION_CHECKS.get(section_label)
    if not keys:
        return False
    if section_label == "Certificate or Witness":
        return any(_value_present(read_model.get(key)) for key in keys)
    if section_label == "Reproduce / Verify":
        return _value_present(read_model.get("reproduce_commands")) or _value_present(
            read_model.get("verify_commands"),
        )
    if section_label == "Limitations":
        return _value_present(read_model.get("limitations")) or _value_present(
            read_model.get("limitation_notice"),
        )
    key = keys[0]
    return _value_present(read_model.get(key))


def evaluate_section_coverage(
    read_model: dict[str, Any],
    *,
    required: list[str] | None = None,
) -> dict[str, Any]:
    labels = required or list(REQUIRED_INTERPRETABILITY_SECTIONS)
    present: list[str] = []
    missing: list[str] = []
    for label in labels:
        if section_present(read_model, label):
            present.append(label)
        else:
            missing.append(label)
    total = len(labels)
    rendered = len(present)
    return {
        "required_sections": labels,
        "present_sections": present,
        "missing_sections": missing,
        "required_sections_rendered": rendered / total if total else 0.0,
        "required_sections_rendered_count": rendered,
        "required_sections_total": total,
    }


def count_render_metrics(read_model: dict[str, Any]) -> dict[str, Any]:
    registry = read_model.get("artifact_registry") or []
    handoffs = read_model.get("handoff_manifests") or []
    kernel = read_model.get("formal_trust_kernel") or {}
    limitations = read_model.get("limitations") or []
    lineage = read_model.get("lineage") or {}
    staleness = read_model.get("staleness") or {}
    validation = read_model.get("release_chain_validation") or {}
    checks = validation.get("checks") or []

    formal_rows = 0
    if isinstance(kernel, dict):
        formal_rows = len(kernel.get("lean_check_results") or [])

    return {
        "artifact_rows_rendered": len(registry) if isinstance(registry, list) else 0,
        "registry_metadata_rendered": (
            1.0
            if isinstance(registry, list)
            and registry
            and isinstance(registry[0], dict)
            and registry[0].get("admission_status")
            else 0.0
        ),
        "handoffs_rendered": len(handoffs) if isinstance(handoffs, list) else 0,
        "formal_checks_rendered": formal_rows,
        "limitations_rendered": len(limitations) if isinstance(limitations, list) else 0,
        "lineage_records_created": 1 if isinstance(lineage, dict) and lineage.get("claim_id") else 0,
        "staleness_detected": 1 if isinstance(staleness, dict) and "stale" in staleness else 0,
        "release_chain_checks_rendered": len(checks) if isinstance(checks, list) else 0,
    }
