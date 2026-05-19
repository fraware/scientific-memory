#!/usr/bin/env python3
"""Build computation-release fixtures (passed + rejected witness) for Scientific Memory PCS tests."""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "pipeline" / "src"))

from sm_pipeline.pcs_validate.canonical_hash import SIGNATURE_FIELD, canonical_hash, file_sha256_digest

PCS_CORE = "a361fd2b388f88cdbc9e4e4691ae49dba714ab6c"
RUNNER = "4c5439ae358733f9a4c4a58e33fdaed1ab0d29de"
PF = "0f659b90c80c46a6bbfd51b0d37ea723b032fb9d"
CE = "cb6848001e2e60a484e04eba5ad6be3fe2e4eccc"
SM = "796bb99cb79fe7b195fd156feb346c08fc334d33"
WORKFLOW_ID = "scientific_computation.reproducibility_v0"
RELEASE_ID = "release-pcs-v0.1-scientific-computation-reproducibility"
CLAIM_ID = "claim-computation-release-v0.1"


def _sign(data: dict) -> dict:
    signed = dict(data)
    signed[SIGNATURE_FIELD] = "sha256:" + "0" * 64
    signed[SIGNATURE_FIELD] = canonical_hash(signed)
    return signed


def _build_chain(*, rejected: bool) -> dict[str, dict]:
    files = [
        {
            "path": "data/measurements.csv",
            "sha256": "sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            "size_bytes": 128,
            "media_type": "text/csv",
        },
    ]
    aggregate_hash = canonical_hash({"files": files})
    dataset = _sign(
        {
            "schema_version": "v0",
            "dataset_id": "dataset-demo-measurements-v0.1",
            "dataset_name": "Demo measurements",
            "dataset_version": "v0.1.0",
            "files": files,
            "aggregate_hash": aggregate_hash,
            "source_uri": "https://example.org/datasets/demo-measurements/v0.1.0",
            "source_repo": "https://github.com/example/scientific-computation-runner",
            "source_commit": RUNNER,
            "license": "CC-BY-4.0",
            "created_at": "2026-05-18T12:00:00Z",
        },
    )
    environment = _sign(
        {
            "schema_version": "v0",
            "environment_id": "env-linux-py312-uv",
            "environment_kind": "uv",
            "os": "linux",
            "architecture": "x86_64",
            "language_runtimes": ["python-3.12"],
            "packages": ["numpy==2.1.0", "pandas==2.2.0"],
            "container_image": "ghcr.io/example/scientific-runner:py312",
            "container_digest": "sha256:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
            "hardware_summary": "4 vCPU, 16 GiB RAM",
            "source_repo": "https://github.com/example/scientific-computation-runner",
            "source_commit": RUNNER,
        },
    )
    run = _sign(
        {
            "schema_version": "v0",
            "run_id": "run-demo-analysis-001",
            "workflow_id": WORKFLOW_ID,
            "command": "uv run python -m demo_analysis --input data/measurements.csv",
            "code_repo": "https://github.com/example/scientific-computation-runner",
            "code_commit": RUNNER,
            "dataset_receipt_ref": dataset["dataset_id"],
            "environment_receipt_ref": environment["environment_id"],
            "started_at": "2026-05-18T12:05:00Z",
            "completed_at": "2026-05-18T12:06:30Z",
            "exit_code": 0,
            "stdout_hash": "sha256:cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
            "stderr_hash": "sha256:dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd",
            "result_artifact_refs": ["result-demo-summary-v0.1"],
            "source_repo": "https://github.com/example/scientific-computation-runner",
            "source_commit": RUNNER,
        },
    )
    result = _sign(
        {
            "schema_version": "v0",
            "result_id": "result-demo-summary-v0.1",
            "result_kind": "table",
            "path": "outputs/summary.parquet",
            "sha256": "sha256:eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",
            "size_bytes": 4096,
            "media_type": "application/vnd.apache.parquet",
            "description": "Aggregated measurement summary table",
            "produced_by_run": run["run_id"],
            "source_repo": "https://github.com/example/scientific-computation-runner",
            "source_commit": RUNNER,
        },
    )
    witness_status = "Rejected" if rejected else "CertificateChecked"
    bundle_cert_status = "CertificateChecked"
    violations: list[dict] = []
    if rejected:
        violations = [
            {
                "violation_id": "viol-result-hash-mismatch",
                "violation_type": "result_hash_mismatch",
                "explanation": (
                    "Re-run with the pinned dataset version and verify result artifact "
                    "sha256:eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee."
                ),
                "expected_hash": result["sha256"],
                "actual_hash": "sha256:ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff",
                "responsible_component": "scientific-computation-runner",
            },
        ]
    witness = _sign(
        {
            "schema_version": "v0",
            "witness_id": "witness-computation-demo-v0.1",
            "workflow_id": WORKFLOW_ID,
            "dataset_hash": dataset["aggregate_hash"],
            "environment_hash": environment[SIGNATURE_FIELD],
            "run_receipt_hash": run[SIGNATURE_FIELD],
            "result_hashes": [result["sha256"]],
            "code_repo": "https://github.com/example/scientific-computation-runner",
            "code_commit": RUNNER,
            "checker": "pcs-core-computation-validator",
            "checker_version": "0.1.0",
            "status": witness_status,
            "violations": violations,
            "source_repo": "https://github.com/SentinelOps-CI/pcs-core",
            "source_commit": PCS_CORE,
        },
    )
    return {
        "dataset_receipt.json": dataset,
        "environment_receipt.json": environment,
        "computation_run_receipt.json": run,
        "result_artifact.json": result,
        "computation_witness.json": witness,
    }


def _write_dir(target: Path, *, rejected: bool) -> None:
    tool_use = REPO_ROOT / "tests" / "pcs" / "fixtures" / "tool-use-release"
    if not tool_use.is_dir():
        raise SystemExit(f"missing tool-use fixture template: {tool_use}")

    target.mkdir(parents=True, exist_ok=True)
    chain = _build_chain(rejected=rejected)

    for name, doc in chain.items():
        (target / name).write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")

    for name in (
        "science_claim_bundle.certified.json",
        "verification_result.json",
        "signed_science_claim_bundle.json",
        "release_chain_validation_result.v0.json",
        "ArtifactRegistry.v0.json",
    ):
        shutil.copy2(tool_use / name, target / name)

    # workflow profile from pcs-core or embedded
    profile_src = REPO_ROOT.parent / "pcs-core" / "examples" / "workflow_profiles" / (
        "scientific_computation_reproducibility.valid.json"
    )
    if profile_src.is_file():
        shutil.copy2(profile_src, target / "workflow_profile.v0.json")
    else:
        (target / "workflow_profile.v0.json").write_text(
            json.dumps(
                {
                    "schema_version": "v0",
                    "workflow_id": WORKFLOW_ID,
                    "domain": "scientific_computation",
                    "description": "Proof-carrying computational reproducibility for declared inputs, environment, command, and results.",
                    "runtime_artifacts": [
                        "DatasetReceipt.v0",
                        "EnvironmentReceipt.v0",
                        "ComputationRunReceipt.v0",
                        "ResultArtifact.v0",
                    ],
                    "certificate_artifacts": ["ComputationWitness.v0"],
                    "limitations_notice": (
                        "This artifact verifies declared computational provenance and hash consistency. "
                        "It does not prove that the dataset is unbiased, that the model is scientifically valid, "
                        "or that the result generalizes beyond the declared inputs and environment."
                    ),
                    "signature_or_digest": "sha256:" + "0" * 64,
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        profile = json.loads((target / "workflow_profile.v0.json").read_text(encoding="utf-8"))
        profile["signature_or_digest"] = canonical_hash(profile)
        (target / "workflow_profile.v0.json").write_text(
            json.dumps(profile, indent=2) + "\n",
            encoding="utf-8",
        )

    witness = chain["computation_witness.json"]
    trace_hash = witness["dataset_hash"]
    bundle_cert_status = "CertificateChecked"
    bundle_path = target / "signed_science_claim_bundle.json"
    bundle = json.loads(bundle_path.read_text(encoding="utf-8-sig"))
    scb = bundle["science_claim_bundle"]
    claim_id = "claim-computation-rejected-v0.1" if rejected else CLAIM_ID
    scb["claim_artifact"] = {
        "artifact_id": claim_id,
        "artifact_type": "ClaimArtifact.v0",
        "schema_version": "v0",
        "claim_text": "The declared computation run reproduces the pinned dataset under the recorded environment.",
        "claim_kind": "scientific_claim",
        "status": bundle_cert_status,
        "assumption_set_ref": scb.get("assumption_set", {}).get("assumption_set_id", "as-computation-v0.1"),
        "source_span_refs": [],
        "formal_statement": "",
        "certificate_refs": [witness["witness_id"]],
        "runtime_receipt_refs": ["receipt-computation-run-001"],
        "created_at": "2026-05-18T12:05:00Z",
        "producer": "scientific-computation-runner",
        "producer_version": "0.1.0",
        "source_repo": "https://github.com/example/scientific-computation-runner",
        "source_commit": RUNNER,
        "signature_or_digest": "sha256:2222222222222222222222222222222222222222222222222222222222222222",
    }
    receipts = scb.get("runtime_receipts")
    if isinstance(receipts, list) and receipts and isinstance(receipts[0], dict):
        merged = dict(receipts[0])
        merged.update(
            {
                "receipt_id": "receipt-computation-run-001",
                "run_id": chain["computation_run_receipt.json"]["run_id"],
                "started_at": chain["computation_run_receipt.json"]["started_at"],
                "ended_at": chain["computation_run_receipt.json"]["completed_at"],
                "trace_hash": trace_hash,
                "producer": "scientific-computation-runner",
                "source_repo": "https://github.com/example/scientific-computation-runner",
                "source_commit": RUNNER,
            },
        )
        scb["runtime_receipts"] = [merged]
    else:
        scb["runtime_receipts"] = [
            {
                "receipt_id": "receipt-computation-run-001",
                "schema_version": "v0",
                "run_id": chain["computation_run_receipt.json"]["run_id"],
                "environment": {"platform": "linux", "python": "3.12"},
                "started_at": chain["computation_run_receipt.json"]["started_at"],
                "ended_at": chain["computation_run_receipt.json"]["completed_at"],
                "status": "RuntimeObserved",
                "run_outcome": "passed",
                "final_reason_code": "ok",
                "released": True,
                "events_hash": "sha256:3333333333333333333333333333333333333333333333333333333333333333",
                "policy_hash": "sha256:4444444444444444444444444444444444444444444444444444444444444444",
                "trace_hash": trace_hash,
                "input_hashes": {"dataset": trace_hash},
                "output_hashes": {"result": chain["result_artifact.json"]["sha256"]},
                "producer": "scientific-computation-runner",
                "producer_version": "0.1.0",
                "source_repo": "https://github.com/example/scientific-computation-runner",
                "source_commit": RUNNER,
                "signature_or_digest": chain["computation_run_receipt.json"]["signature_or_digest"],
            },
        ]
    certs = scb.get("certificates")
    if isinstance(certs, list) and certs and isinstance(certs[0], dict):
        cert = dict(certs[0])
        cert.update(
            {
                "certificate_id": witness["witness_id"],
                "trace_hash": trace_hash,
                "property_id": "scientific_computation.reproducibility_v0",
                "checker": witness["checker"],
                "checker_version": witness["checker_version"],
                "status": bundle_cert_status,
                "source_repo": witness["source_repo"],
                "source_commit": witness["source_commit"],
                "signature_or_digest": witness["signature_or_digest"],
            },
        )
        scb["certificates"] = [cert]
    else:
        scb["certificates"] = [
            {
                "certificate_id": witness["witness_id"],
                "schema_version": "v0",
                "trace_hash": trace_hash,
                "spec_hash": trace_hash,
                "property_id": "scientific_computation.reproducibility_v0",
                "checker": witness["checker"],
                "checker_version": witness["checker_version"],
                "status": bundle_cert_status,
                "counterexample_ref": None,
                "created_at": "2026-05-18T12:10:00Z",
                "producer": witness["checker"],
                "producer_version": witness["checker_version"],
                "source_repo": witness["source_repo"],
                "source_commit": witness["source_commit"],
                "signature_or_digest": witness["signature_or_digest"],
            },
        ]
    bundle_path.write_text(json.dumps(bundle, indent=2) + "\n", encoding="utf-8")
    shutil.copy2(bundle_path, target / "science_claim_bundle.certified.json")

    artifacts = {
        name: file_sha256_digest(target / name) for name in chain
    }
    artifacts["workflow_profile.v0.json"] = file_sha256_digest(target / "workflow_profile.v0.json")
    artifacts["science_claim_bundle.certified.json"] = file_sha256_digest(
        target / "science_claim_bundle.certified.json",
    )
    artifacts["verification_result.json"] = file_sha256_digest(target / "verification_result.json")
    artifacts["signed_science_claim_bundle.json"] = file_sha256_digest(bundle_path)

    manifest = {
        "schema_version": "v0",
        "release_id": RELEASE_ID if not rejected else "release-pcs-v0.1-scientific-computation-rejected",
        "release_candidate": "pcs-v0.1-scientific-computation-conformance",
        "generated_at": "2026-05-18T12:00:00Z",
        "validation_profile": WORKFLOW_ID,
        "workflow_profile_id": WORKFLOW_ID,
        "chain_root": {
            "trace_hash": witness["dataset_hash"],
            "certificate_id": witness["witness_id"],
            "certified_bundle_hash": artifacts["science_claim_bundle.certified.json"],
            "signed_bundle_hash": artifacts["signed_science_claim_bundle.json"],
        },
        "release_chain_validation_result": {
            "path": "release_chain_validation_result.v0.json",
            "sha256": file_sha256_digest(target / "release_chain_validation_result.v0.json"),
        },
        "canonical_signed_bundle": {
            "path": "signed_science_claim_bundle.json",
            "sha256": artifacts["signed_science_claim_bundle.json"],
        },
        "canonical_claim_id": claim_id,
        "limitations_notice": (
            "This artifact verifies declared computational provenance and hash consistency. "
            "It does not prove that the dataset is unbiased, that the model is scientifically valid, "
            "or that the result generalizes beyond the declared inputs and environment."
        ),
        "producer_repos": {
            "pcs_core": {"repo": "https://github.com/SentinelOps-CI/pcs-core", "commit": PCS_CORE},
            "scientific_computation": {
                "repo": "https://github.com/example/scientific-computation-runner",
                "commit": RUNNER,
            },
            "certifyedge": {"repo": "https://github.com/fraware/CertifyEdge", "commit": CE},
            "provability_fabric": {
                "repo": "https://github.com/SentinelOps-CI/provability-fabric",
                "commit": PF,
            },
            "scientific_memory": {
                "repo": "https://github.com/fraware/scientific-memory",
                "commit": SM,
            },
        },
        "artifacts": {},
        "release_status": "Validated",
    }
    for name, digest in artifacts.items():
        manifest["artifacts"][name] = {
            "artifact_type": _artifact_type(name),
            "schema": f"schemas/{_artifact_type(name).replace('.v0', '.v0.schema.json')}",
            "producer": "pcs-core",
            "source_repo": "https://github.com/SentinelOps-CI/pcs-core",
            "source_commit": PCS_CORE,
            "sha256": digest,
        }
    manifest["signature_or_digest"] = canonical_hash(manifest)
    (target / "release_manifest.v0.json").write_text(
        json.dumps(manifest, indent=2) + "\n",
        encoding="utf-8",
    )
    (target / "ReleaseManifest.v0.json").write_text(
        (target / "release_manifest.v0.json").read_text(encoding="utf-8"),
        encoding="utf-8",
    )

    import_report = {
        "allow_legacy": False,
        "bundle_shape": "pcs_core",
        "claim_id": claim_id,
        "imported_at": "2026-05-18T12:10:00Z",
        "render_path": f"/pcs/claims/{claim_id}",
        "scientific_memory_commit": SM,
        "source_commit": SM,
        "source_repo": "https://github.com/fraware/scientific-memory",
        "strict": True,
        "verification_status": "passed",
        "warnings": [],
        "release_id": manifest["release_id"],
        "release_candidate": manifest["release_candidate"],
        "release_manifest_path": str(target.relative_to(REPO_ROOT)).replace("\\", "/")
        + "/release_manifest.v0.json",
        "validation_profile": WORKFLOW_ID,
        "workflow_profile_id": WORKFLOW_ID,
        "release_chain_validation_status": "ProofChecked",
        "release_chain_validator": "pcs-core",
        "release_chain_checked_at": "2026-05-18T12:00:00Z",
    }
    (target / "scientific_memory_import_report.json").write_text(
        json.dumps(import_report, indent=2) + "\n",
        encoding="utf-8",
    )

    deferred_refs = [
        "DatasetReceipt.v0.signature_or_digest_valid",
        "DatasetReceipt.v0.source_commit_not_placeholder",
        "EnvironmentReceipt.v0.signature_or_digest_valid",
        "EnvironmentReceipt.v0.source_commit_not_placeholder",
        "ComputationRunReceipt.v0.signature_or_digest_valid",
        "ComputationRunReceipt.v0.source_commit_not_placeholder",
        "ResultArtifact.v0.signature_or_digest_valid",
        "ResultArtifact.v0.source_commit_not_placeholder",
        "ComputationWitness.v0.signature_or_digest_valid",
        "ComputationWitness.v0.code_commit_present",
        "ComputationWitness.v0.dataset_hash_matches_receipt",
        "ComputationWitness.v0.environment_hash_matches_receipt",
        "ComputationWitness.v0.run_receipt_hash_matches_declared_run",
        "ComputationWitness.v0.result_hashes_match_result_artifacts",
        "ReleaseManifest.v0.artifact_hashes_match_files",
        "ReleaseManifest.v0.release_mode_commit_policy",
        "HandoffManifest.v0.handoff_input_hashes_when_validated",
        "ScienceClaimBundle.v0.non_empty_runtime_receipts",
        "ScienceClaimBundle.v0.certified_bundle_has_certificate_when_checked",
        "VerificationResult.v0.verified_input_bundle_hash_matches_certified",
        "VerificationResult.v0.failed_checks_block_import_ready_status",
        "SignedScienceClaimBundle.v0.signed_input_bundle_hash_matches_certified",
    ]
    validation = {
        "schema_version": "v0",
        "validation_id": f"validation-{manifest['release_id']}",
        "release_id": manifest["release_id"],
        "release_candidate": manifest["release_candidate"],
        "workflow_profile_id": WORKFLOW_ID,
        "validator": "pcs-core",
        "validator_version": "0.1.0",
        "checked_at": "2026-05-18T12:00:00Z",
        "status": "ProofChecked",
        "checks": [
            {
                "check_id": "release_manifest_integrity",
                "description": "Release manifest artifact hashes match files",
                "status": "passed",
                "details": {},
                "registry_check_refs": ["ReleaseManifest.v0.artifact_hashes_match_files"],
                "responsible_component": "pcs-core",
            },
            {
                "check_id": "science_claim_bundle_semantics",
                "description": "Science claim bundle certificate refs present",
                "status": "passed",
                "details": {},
                "registry_check_refs": [
                    "ScienceClaimBundle.v0.non_empty_runtime_receipts",
                    "ScienceClaimBundle.v0.certified_bundle_has_certificate_when_checked",
                ],
                "responsible_component": "pcs-core",
            },
            {
                "check_id": "verification_and_signed_bundle_hashes",
                "description": "Verification and signed bundle hash alignment",
                "status": "passed",
                "details": {},
                "registry_check_refs": [
                    "VerificationResult.v0.verified_input_bundle_hash_matches_certified",
                    "VerificationResult.v0.failed_checks_block_import_ready_status",
                    "SignedScienceClaimBundle.v0.signed_input_bundle_hash_matches_certified",
                ],
                "responsible_component": "Provability Fabric",
            },
            {
                "check_id": "computation_witness_release_status",
                "description": "Computation witness status checked for release",
                "status": "passed",
                "details": {},
                "registry_check_refs": [
                    "ComputationWitness.v0.computation_status_checked_for_release",
                ],
                "responsible_component": "pcs-core",
            },
            {
                "check_id": "computation_witness_source_commit",
                "description": "Computation witness source commit matches manifest",
                "status": "passed",
                "details": {},
                "registry_check_refs": [
                    "ComputationWitness.v0.source_commit_matches_release_manifest",
                ],
                "responsible_component": "pcs-core",
            },
        ],
        "artifacts_checked": len(manifest["artifacts"]),
        "failure_codes": [],
        "source_repo": "https://github.com/SentinelOps-CI/pcs-core",
        "source_commit": PCS_CORE,
        "deferred_registry_checks": [
            {
                "registry_ref": ref,
                "status": "deferred",
                "enforcement_location": "artifact_validate",
                "responsible_component": "pcs-core",
                "reason": "Deferred for scientific-memory computation conformance fixture import.",
            }
            for ref in deferred_refs
            if ref
            not in {
                "ReleaseManifest.v0.artifact_hashes_match_files",
                "ScienceClaimBundle.v0.non_empty_runtime_receipts",
                "ScienceClaimBundle.v0.certified_bundle_has_certificate_when_checked",
                "VerificationResult.v0.verified_input_bundle_hash_matches_certified",
                "VerificationResult.v0.failed_checks_block_import_ready_status",
                "SignedScienceClaimBundle.v0.signed_input_bundle_hash_matches_certified",
                "ComputationWitness.v0.computation_status_checked_for_release",
                "ComputationWitness.v0.source_commit_matches_release_manifest",
            }
        ],
    }
    validation["signature_or_digest"] = canonical_hash(validation)
    validation_path = target / "release_chain_validation_result.v0.json"
    validation_path.write_text(json.dumps(validation, indent=2) + "\n", encoding="utf-8")
    (target / "ReleaseChainValidationResult.v0.json").write_text(
        validation_path.read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    manifest["release_chain_validation_result"]["sha256"] = file_sha256_digest(validation_path)
    import subprocess

    subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "scripts" / "bootstrap_formal_trust_release.py"),
            "--release-dir",
            str(target),
        ],
        cwd=REPO_ROOT,
        check=True,
    )
    for name in ("proof_obligation.v0.json", "lean_check_result.v0.json"):
        path = target / name
        if path.is_file():
            doc = json.loads(path.read_text(encoding="utf-8-sig"))
            manifest["artifacts"][name] = {
                "artifact_type": "ProofObligation.v0" if "obligation" in name else "LeanCheckResult.v0",
                "schema": name.replace(".json", ".schema.json"),
                "producer": "pcs-core",
                "source_repo": str(doc.get("source_repo") or "https://github.com/SentinelOps-CI/pcs-core"),
                "source_commit": str(doc.get("source_commit") or PCS_CORE),
                "sha256": file_sha256_digest(path),
            }
    manifest["signature_or_digest"] = canonical_hash(manifest)
    (target / "release_manifest.v0.json").write_text(
        json.dumps(manifest, indent=2) + "\n",
        encoding="utf-8",
    )
    (target / "ReleaseManifest.v0.json").write_text(
        (target / "release_manifest.v0.json").read_text(encoding="utf-8"),
        encoding="utf-8",
    )


def _artifact_type(name: str) -> str:
    mapping = {
        "dataset_receipt.json": "DatasetReceipt.v0",
        "environment_receipt.json": "EnvironmentReceipt.v0",
        "computation_run_receipt.json": "ComputationRunReceipt.v0",
        "result_artifact.json": "ResultArtifact.v0",
        "computation_witness.json": "ComputationWitness.v0",
        "workflow_profile.v0.json": "WorkflowProfile.v0",
        "science_claim_bundle.certified.json": "ScienceClaimBundle.v0",
        "verification_result.json": "VerificationResult.v0",
        "signed_science_claim_bundle.json": "SignedScienceClaimBundle.v0",
    }
    return mapping.get(name, "Unknown.v0")


def main() -> int:
    sys.path.insert(0, str(REPO_ROOT / "scripts"))
    from pcs_phase2_fixture import write_phase2_read_model_fixture

    passed_dir = REPO_ROOT / "tests" / "pcs" / "fixtures" / "computation-release"
    rejected_dir = REPO_ROOT / "tests" / "pcs" / "fixtures" / "computation-rejected-release"
    examples_dir = REPO_ROOT / "examples" / "computation-release"
    _write_dir(passed_dir, rejected=False)
    _write_dir(rejected_dir, rejected=True)
    examples_dir.mkdir(parents=True, exist_ok=True)
    for path in passed_dir.iterdir():
        if path.is_file():
            shutil.copy2(path, examples_dir / path.name)
    for release_dir in (passed_dir, rejected_dir):
        out = write_phase2_read_model_fixture(release_dir, repo_root=REPO_ROOT)
        print(f"wrote portal contract fixture -> {out}")
    print(f"OK: {passed_dir}")
    print(f"OK: {rejected_dir}")
    print(f"OK: {examples_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
