#!/usr/bin/env python3
"""Generate benchmarks/rendering/*/expected_*.json from PCS fixtures."""

from __future__ import annotations

import json
import shutil
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "pipeline" / "src"))

from sm_pipeline.benchmark.pcs_sections import REQUIRED_INTERPRETABILITY_SECTIONS, evaluate_section_coverage
from sm_pipeline.benchmark.rendering import _copy_pcs_schemas, _resolve_manifest_path
from sm_pipeline.pcs_import.claim_query import refresh_all_stale_flags
from sm_pipeline.pcs_import.release_compare import compare_releases
from sm_pipeline.pcs_import.release_manifest_importer import import_release_manifest

BENCHMARKS = REPO_ROOT / "benchmarks" / "rendering"

CASE_DEFS: list[dict] = [
    {
        "case_id": "labtrust_qc_release",
        "dir": "labtrust_qc_release",
        "fixture_dir": "tests/pcs/fixtures/labtrust-release",
        "manifest_filename": "ReleaseManifest.v0.json",
        "claim_id": "claim-pcs-qc-release-v0.1",
        "release_id": "release-pcs-v0.1-labtrust-qc",
        "workflow_id": "labtrust.qc_release_v0.1",
        "certificate_id": "cert-trace-a1b8ff9d-7d5f-489c-98b1-a3a630cb87d7",
        "source_commit": "8369892d8872bc08ef5acb6cf503f38665c36733",
        "lean_theorem": "PCS.CertificateMatchesRuntime",
        "compare": {
            "old_release_id": "release-pcs-v0.1-labtrust-qc",
            "new_release_id": "release-pcs-v0.1-scientific-computation-reproducibility",
            "second_fixture_dir": "tests/pcs/fixtures/computation-release",
            "manifest_filename": "release_manifest.v0.json",
            "second_claim_id": "claim-computation-release-v0.1",
        },
    },
    {
        "case_id": "tool_use_safety",
        "dir": "tool_use_safety",
        "fixture_dir": "tests/pcs/fixtures/tool-use-release",
        "manifest_filename": "release_manifest.v0.json",
        "claim_id": "claim-qc-release-v0.1",
        "release_id": "release-pcs-v0.1-tool-use-safety",
        "workflow_id": "agent_tool_use.safety_v0",
        "certificate_id": "cert-tool-use-safety-v0",
        "source_commit": "4c5439ae358733f9a4c4a58e33fdaed1ab0d29de",
        "lean_theorem": "PCS.VerificationAdmitsBundle",
    },
    {
        "case_id": "computation_reproducibility",
        "dir": "computation_reproducibility",
        "fixture_dir": "tests/pcs/fixtures/computation-release",
        "manifest_filename": "release_manifest.v0.json",
        "claim_id": "claim-computation-release-v0.1",
        "release_id": "release-pcs-v0.1-scientific-computation-reproducibility",
        "workflow_id": "scientific_computation.reproducibility_v0",
        "certificate_id": "witness-computation-demo-v0.1",
        "source_commit": "4c5439ae358733f9a4c4a58e33fdaed1ab0d29de",
        "dataset_id": "dataset-demo-measurements-v0.1",
        "result_hash": "sha256:eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",
        "lean_theorem": "PCS.SignedBundleAdmissible",
    },
]

FAILED_CASE_DEFS: list[dict] = [
    {
        "case_id": "rejected_certificate",
        "dir": "failed/rejected_certificate",
        "fixture_dir": "tests/pcs/fixtures/computation-rejected-release",
        "manifest_filename": "release_manifest.v0.json",
        "claim_id": "claim-computation-rejected-v0.1",
        "release_id": "release-pcs-v0.1-scientific-computation-rejected",
    },
    {
        "case_id": "stale_release",
        "dir": "failed/stale_release",
        "fixture_dir": "tests/pcs/fixtures/labtrust-release",
        "manifest_filename": "ReleaseManifest.v0.json",
        "claim_id": "claim-pcs-qc-release-v0.1",
        "release_id": "release-pcs-v0.1-labtrust-qc",
        "post_import": "mark_stale",
    },
    {
        "case_id": "failed_lean_check",
        "dir": "failed/failed_lean_check",
        "fixture_dir": "tests/pcs/fixtures/labtrust-release",
        "manifest_filename": "ReleaseManifest.v0.json",
        "claim_id": "claim-pcs-qc-release-v0.1",
        "release_id": "release-pcs-v0.1-labtrust-qc",
        "post_import": "patch_lean_failed",
    },
    {
        "case_id": "failed_pf_verification",
        "dir": "failed/failed_pf_verification",
        "fixture_dir": "tests/pcs/fixtures/labtrust-release",
        "manifest_filename": "ReleaseManifest.v0.json",
        "claim_id": "claim-pcs-qc-release-v0.1",
        "release_id": "release-pcs-v0.1-labtrust-qc",
        "post_import": "patch_pf_failed",
    },
    {
        "case_id": "missing_registry_metadata",
        "dir": "failed/missing_registry_metadata",
        "fixture_dir": "tests/pcs/fixtures/labtrust-release",
        "manifest_filename": "ReleaseManifest.v0.json",
        "claim_id": "claim-pcs-qc-release-v0.1",
        "release_id": "release-pcs-v0.1-labtrust-qc",
        "post_import": "deferred_registry_only",
    },
]


def _apply_post_import(root: Path, release_dir: Path, case_def: dict) -> None:
    post = str(case_def.get("post_import") or "")
    claim_id = case_def["claim_id"]
    claim_dir = root / "corpus" / "pcs" / "claims" / claim_id
    manifest = _resolve_manifest_path(release_dir, case_def)

    if post == "mark_stale":
        bundle = claim_dir / "signed_bundle.json"
        bundle.write_bytes(bundle.read_bytes() + b"\n")
        refresh_all_stale_flags(root)
        read_model_path = claim_dir / "read_model.json"
        if read_model_path.is_file():
            read_model = json.loads(read_model_path.read_text(encoding="utf-8"))
            staleness = read_model.get("staleness")
            if isinstance(staleness, dict):
                staleness["responsible_component"] = "Scientific Memory"
            read_model_path.write_text(json.dumps(read_model, indent=2) + "\n", encoding="utf-8")
        return

    if post in ("patch_lean_failed", "patch_pf_failed"):
        read_model_path = claim_dir / "read_model.json"
        if read_model_path.is_file():
            read_model = json.loads(read_model_path.read_text(encoding="utf-8"))
            kernel = read_model.get("formal_trust_kernel")
            if isinstance(kernel, dict):
                results = kernel.get("lean_check_results") or []
                if results and isinstance(results[0], dict):
                    results[0]["result"] = "failed"
                    results[0]["status"] = "Failed"
                    results[0]["repair_hint"] = "Align trace_certificate trace_hash with runtime_receipt."
                    results[0]["responsible_component"] = "Provability Fabric"
                    results[0]["pf_explain"] = "bundle_hash mismatch in verified_input"
                kernel["overall_status"] = "Failed"
                read_model_path.write_text(json.dumps(read_model, indent=2) + "\n", encoding="utf-8")
        return

    if post == "deferred_registry_only":
        read_model_path = claim_dir / "read_model.json"
        if read_model_path.is_file():
            read_model = json.loads(read_model_path.read_text(encoding="utf-8"))
            validation = read_model.get("release_chain_validation")
            if isinstance(validation, dict):
                checks = validation.get("checks") or []
                validation["deferred_registry_checks"] = [
                    str(c.get("check_id") or "registry_semantic")
                    for c in checks[:2]
                    if isinstance(c, dict)
                ]
            registry = read_model.get("artifact_registry") or []
            if isinstance(registry, list):
                for row in registry:
                    if isinstance(row, dict) and row.get("admission_status") == "passed":
                        row["admission_status"] = "deferred"
            read_model_path.write_text(json.dumps(read_model, indent=2) + "\n", encoding="utf-8")
        return


def _import_in_temp(case_def: dict) -> tuple[dict, dict, Path]:
    fixture_src = (REPO_ROOT / case_def["fixture_dir"]).resolve()
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _copy_pcs_schemas(root, REPO_ROOT)
        release_dir = root / "release"
        shutil.copytree(fixture_src, release_dir)
        local = {**case_def, "fixture_dir": "release"}
        manifest = _resolve_manifest_path(release_dir, local)
        import_release_manifest(manifest, repo_root=root, write=True, render=False)
        if case_def.get("post_import"):
            _apply_post_import(root, release_dir, local)
        claim_id = case_def["claim_id"]
        read_model = json.loads(
            (root / "corpus" / "pcs" / "claims" / claim_id / "read_model.json").read_text(encoding="utf-8"),
        )
        lineage = json.loads(
            (root / "corpus" / "pcs" / "claims" / claim_id / "lineage.json").read_text(encoding="utf-8"),
        )
        # persist temp workspace for compare second import
        persist = REPO_ROOT / "benchmark_runs" / "_bootstrap_work" / case_def["case_id"]
        if persist.exists():
            shutil.rmtree(persist)
        shutil.copytree(root, persist)
        return read_model, lineage, persist


def _queries_for(case_def: dict, claim_id: str) -> dict:
    queries: list[dict] = [
        {"id": "list_claims", "type": "list_claims", "params": {}, "expected_claim_ids": [claim_id]},
        {
            "id": "by_release",
            "type": "by_release",
            "params": {"release_id": case_def["release_id"]},
            "expected_claim_ids": [claim_id],
        },
    ]
    if case_def.get("workflow_id"):
        queries.append(
            {
                "id": "by_workflow",
                "type": "by_workflow",
                "params": {"workflow_id": case_def["workflow_id"]},
                "expected_claim_ids": [claim_id],
            },
        )
    if case_def.get("certificate_id"):
        queries.append(
            {
                "id": "by_certificate",
                "type": "by_certificate",
                "params": {"certificate_id": case_def["certificate_id"]},
                "expected_claim_ids": [claim_id],
            },
        )
    if case_def.get("source_commit"):
        queries.append(
            {
                "id": "by_source_commit",
                "type": "by_source_commit",
                "params": {"commit": case_def["source_commit"]},
                "expected_claim_ids": [claim_id],
            },
        )
    if case_def.get("dataset_id"):
        queries.append(
            {
                "id": "by_dataset",
                "type": "by_dataset",
                "params": {"dataset_id": case_def["dataset_id"]},
                "expected_claim_ids": [claim_id],
            },
        )
    if case_def.get("result_hash"):
        queries.append(
            {
                "id": "by_result_hash",
                "type": "by_result_hash",
                "params": {"hash": case_def["result_hash"]},
                "expected_claim_ids": [claim_id],
            },
        )
    if case_def.get("lean_theorem"):
        queries.append(
            {
                "id": "by_lean_theorem",
                "type": "by_lean_theorem",
                "params": {"theorem": case_def["lean_theorem"]},
                "expected_claim_ids": [claim_id],
            },
        )
    return {"queries": queries}


def _write_case(case_def: dict, *, failed: bool = False) -> None:
    case_dir = BENCHMARKS / case_def["dir"]
    case_dir.mkdir(parents=True, exist_ok=True)

    config: dict = {
        "case_id": case_def["case_id"],
        "fixture_dir": case_def["fixture_dir"],
        "manifest_filename": case_def["manifest_filename"],
        "claim_id": case_def["claim_id"],
        "release_id": case_def["release_id"],
    }
    if case_def.get("workflow_id"):
        config["workflow_id"] = case_def["workflow_id"]
    if case_def.get("compare"):
        config["compare"] = case_def["compare"]
    if case_def.get("post_import"):
        config["post_import"] = case_def["post_import"]
    if failed:
        config["failure_mode"] = True
    (case_dir / "case.json").write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")

    release_dir = (REPO_ROOT / case_def["fixture_dir"]).resolve()
    manifest_src = _resolve_manifest_path(release_dir, case_def)
    shutil.copy(manifest_src, case_dir / "release_manifest.v0.json")

    read_model, lineage, work_root = _import_in_temp(case_def)
    claim_id = case_def["claim_id"]

    section = evaluate_section_coverage(read_model)
    (case_dir / "expected_sections.json").write_text(
        json.dumps(
            {
                "required_sections": list(REQUIRED_INTERPRETABILITY_SECTIONS),
                "present_sections": section["present_sections"],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    lineage_expected: dict = {
        "claim_id": claim_id,
        "release_id": case_def["release_id"],
        "has_signed_bundle_hash": True,
    }
    if case_def.get("certificate_id"):
        lineage_expected["certificate_id"] = case_def["certificate_id"]
    (case_dir / "expected_lineage.json").write_text(
        json.dumps(lineage_expected, indent=2) + "\n",
        encoding="utf-8",
    )

    staleness_expected: dict = {"stale": False}
    if case_def.get("post_import") == "mark_stale":
        staleness_expected = {"stale": True, "claim_state": "stale", "requires_repair_hint": True}
    (case_dir / "expected_staleness.json").write_text(
        json.dumps(staleness_expected, indent=2) + "\n",
        encoding="utf-8",
    )

    if case_def.get("compare"):
        cmp = case_def["compare"]
        second_dir = (REPO_ROOT / cmp["second_fixture_dir"]).resolve()
        second_manifest = _resolve_manifest_path(second_dir, cmp)
        import_release_manifest(second_manifest, repo_root=work_root, write=True, render=False)
        payload = compare_releases(
            work_root,
            old_release_id=cmp["old_release_id"],
            new_release_id=cmp["new_release_id"],
        )
        (case_dir / "expected_compare.json").write_text(
            json.dumps(
                {
                    "old_release_id": cmp["old_release_id"],
                    "new_release_id": cmp["new_release_id"],
                    "changed_artifacts": bool(payload.get("changed_artifacts")),
                    "changed_hashes": bool(payload.get("changed_hashes")),
                    "changed_source_commits": bool(payload.get("changed_source_commits")),
                    "changed_certificates": bool(payload.get("changed_certificates")),
                    "changed_workflow_profile": bool(payload.get("changed_workflow_profile")),
                    "changed_registry_checks": bool(payload.get("changed_registry_checks")),
                    "changed_formal_checks": bool(payload.get("changed_formal_checks")),
                    "staleness_impact": bool(payload.get("staleness_impact")),
                    "recommended_action": bool(payload.get("recommended_action")),
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

    (case_dir / "expected_queries.json").write_text(
        json.dumps(_queries_for(case_def, claim_id), indent=2) + "\n",
        encoding="utf-8",
    )

    if failed:
        required_checks = [
            "failure_reason_present",
            "artifact_path_present",
            "repair_hint_present",
            "non_claims_present",
            "partial_import_present",
        ]
        if case_def.get("case_id") in (
            "rejected_certificate",
            "failed_lean_check",
            "failed_pf_verification",
            "stale_release",
        ):
            required_checks.insert(1, "responsible_component_present")
        (case_dir / "expected_failure.json").write_text(
            json.dumps({"required_checks": required_checks}, indent=2) + "\n",
            encoding="utf-8",
        )

    if work_root.exists():
        shutil.rmtree(work_root)


def main() -> None:
    for case_def in CASE_DEFS:
        _write_case(case_def, failed=False)
    for case_def in FAILED_CASE_DEFS:
        _write_case(case_def, failed=True)
    print(f"Wrote PCS rendering benchmarks under {BENCHMARKS}")


if __name__ == "__main__":
    main()
