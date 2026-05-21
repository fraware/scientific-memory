# PCS rendering contract

Every PCS claim page at `/pcs/claims/<claim_id>` must render release evidence in a **domain-neutral** layout. LabTrust QC and agent tool-use safety are workflow profiles; the portal does not hardcode LabTrust labels in shared components.

## Section order

| # | Section title | Component | Data source |
|---|---------------|-----------|-------------|
| 1 | Claim | `ClaimArtifactView` | `read_model.claim` |
| 2 | Workflow Profile | `WorkflowProfileView` | `read_model.workflow_profile` |
| 3 | Assumptions | `AssumptionSetView` | `read_model.assumption_set` |
| 4 | Runtime Evidence | `RuntimeReceiptView` | `read_model.runtime_receipt` (hidden when `domain === scientific_computation`) |
| 5 | Dataset Receipt | `DatasetReceiptView` | `read_model.dataset_receipt` (computation workflow) |
| 6 | Environment Receipt | `EnvironmentReceiptView` | `read_model.environment_receipt` (computation workflow) |
| 7 | Computation Run Receipt | `ComputationRunReceiptView` | `read_model.computation_run_receipt` (computation workflow) |
| 8 | Result Artifact | `ResultArtifactView` | `read_model.result_artifact` (computation workflow) |
| 9 | Computation Witness | `ComputationWitnessView` | `read_model.computation_witness` (computation workflow; rejected witnesses show failure panel) |
| 10 | Tool-Use Trace | `ToolUseTraceView` | `read_model.tool_use_trace` (when present) |
| 11 | Tool-Use Certificate | `ToolUseCertificateView` | `read_model.tool_use_certificate` (when present) |
| 12 | Temporal Certificate | `TraceCertificateView` | `read_model.trace_certificate` (when profile lists `TraceCertificate.v0`) |
| 13 | Verification Result | `VerificationResultView` | `read_model.verification_result` |
| 14 | Formal Trust Kernel | `FormalTrustKernelView` | `read_model.formal_trust_kernel` (when workflow requires formal trust) |
| 15 | Release Manifest | `ReleaseManifestView` | `read_model.release_manifest` |
| 16 | Release Chain Validation | `ReleaseChainValidationView` | `read_model.release_chain_validation` |
| 17 | Artifact Registry | `ArtifactRegistryView` | `read_model.artifact_registry` |
| 18 | Handoff Manifests | `HandoffManifestView` | `read_model.handoff_manifests` |
| 19 | Protocol artifacts | `ProtocolArtifactsSection` | `read_model.protocol_artifacts` (generic fallback) |
| 20 | Artifact Dependency Graph | `ArtifactDependencyGraph` | `read_model.artifact_dependency_graph` |
| 21 | Lineage | `LineageView` | `read_model.lineage` |
| 22 | Staleness | `StalenessView` | `read_model.staleness` |
| 23 | Artifact Hashes | `ArtifactHashTable` | `read_model.artifact_hashes`, `canonical_digests` |
| 24 | Source Repositories | `SourceRepositories` | `read_model.source_repositories` |
| 25 | Reproduce / Verify | `ReplayCommand` | `reproduce_commands`, `verify_commands` |
| 26 | Limitations | `LimitationNotice` | `limitation_notice`, `limitations` |

## Workflow-aware read model (top level)

Release imports must populate (in addition to nested `workflow_profile`):

- `workflow_id`, `domain`
- `runtime_artifact_types`, `certificate_artifact_types`
- `tool_use_trace`, `tool_use_certificate` when listed in `ReleaseManifest.v0`
- `formal_trust_kernel` when `ProofObligation.v0` and `LeanCheckResult.v0` are present (workflows with `formal_trust_required` on the profile)
- Computation receipts when `workflow_id` is `scientific_computation.reproducibility_v0`:
  - `dataset_receipt`, `environment_receipt`, `computation_run_receipt`, `result_artifact`, `computation_witness`
  - `runtime_artifact_types`: `DatasetReceipt.v0`, `EnvironmentReceipt.v0`, `ComputationRunReceipt.v0`, `ResultArtifact.v0`
  - `certificate_artifact_types`: `ComputationWitness.v0`

## Computation reproducibility sections

When `domain === scientific_computation` (or workflow `scientific_computation.reproducibility_v0`):

| Section | Fields surfaced |
|---------|-----------------|
| Dataset Receipt | dataset ID, version, files, per-file hashes, aggregate hash, source URI, license |
| Environment Receipt | environment kind, OS, architecture, language runtimes, packages, container image/digest, hardware summary |
| Computation Run Receipt | command, code repo/commit, dataset/environment receipt refs, exit code, started/completed, stdout/stderr hashes, result artifact refs |
| Result Artifact | result kind, path, hash, size, media type, description, produced-by run |
| Computation Witness | witness ID, status, dataset/environment/run/result hashes, checker, violations, repair hints |

**Limitations (required on every computation release page):** `COMPUTATION_LIMITATION_NOTICE` from `sm_pipeline.pcs_import.computation_protocol` — states that the release verifies declared computational provenance and hash consistency only; it does not prove dataset fairness, model validity, or generalization.

**Rejected witnesses:** When `computation_witness.payload.status === "Rejected"`, `ComputationWitnessView` renders a failure panel (`pcs-computation-witness-failures`) with failed check, violating artifact, expected/actual hash, responsible component, and repair hint per violation.

## Formal Trust Kernel (PCS Phase 5)

When `read_model.formal_trust_kernel` is present (strict release import with `ProofObligation.v0` + `LeanCheckResult.v0`):

| Subsection | Fields surfaced |
|------------|-----------------|
| Summary | `what_was_checked`, `overall_status`, `lean_version`, `checked_at`, `checker`, `theorems_checked`, `artifacts_used` |
| Trust-boundary invariants | `trust_boundary_invariants` (one per milestone obligation) |
| Proof obligations | `obligation_id`, `predicate`, `lean_theorem`, `trust_boundary_invariant`, `source_artifacts` |
| Lean check results | per-theorem `result`, `status`, `checked_at`, `lean_version` |
| Formal scope | `formal_scope` (what the Lean package covers) |
| Formal non-claims | `formal_non_claims` (required disclaimers; see below) |
| Failed checks | when `result === "failed"` or `status === "Rejected"`: theorem, obligation, source artifacts, expected/actual, `responsible_component`, `repair_hint`, optional `pf_explain` |

**Required formal non-claims (always shown):**

- The Lean check does not prove the scientific claim is true.
- The Lean check does not prove the dataset is unbiased.
- The Lean check does not prove the model is valid.
- The Lean check proves only the declared PCS trust-envelope invariant.

**Milestone theorems (LabTrust / tool-use / computation profiles):** `PCS.CertificateMatchesRuntime`, `PCS.VerificationAdmitsBundle`, `PCS.SignedBundleAdmissible`, `PCS.RejectedCertificateNotAdmissible`, `PCS.StaleCertificateNotAdmissible`.

Strict import rejects: missing proof/lean artifacts when required, `LeanCheckResult` status other than `ProofChecked`, release/obligation ID mismatch, or any failed obligation result.

## Generic protocol artifact fallback

`ProtocolArtifactView` renders any supplemental manifest artifact with:

- artifact type, schema, status, producer
- source repo, source commit, hash
- semantic checks and limitations (from payload when present)
- full JSON payload

## Artifact registry rows

Each registry row must expose (when available from `ReleaseManifest.v0` + `ArtifactRegistry.v0`):

- `artifact_type`, `schema`, `schema_owner`, `runtime_producer`, `allowed_runtime_producers`
- `producer`, `status`, `allowed_statuses`, `actual_status`
- `hash`, `source_repo`, `source_commit`
- `required_release_fields_present`, `required_release_fields_missing`
- `semantic_checks`, `semantic_checks_performed`
- `registry_admission_result`, `admission_status` (`passed` | `warning` | `failed` | `deferred` | `not_applicable`)
- `consumer_repos`, `canonical_hash_required`, `release_mode_required`

## Lineage and staleness

`lineage` and `staleness` views include operational fields:

- `claim_state`: `current` | `stale` | `superseded` | `withdrawn` | `revalidated`
- `stale_reasons`, `recommended_action`, `repair_hint` (staleness)
- `previous_release_id`, `newer_release_ids`, `changed_artifacts`, `changed_hashes` (lineage, when indexed)

## Release comparison

`pcs-compare-releases` reports: `changed_artifacts`, `changed_hashes`, `changed_source_commits`, `changed_certificates`, `changed_workflow_profile`, `changed_registry_checks`, `changed_formal_checks`, `changed_computation`, `staleness_impact`, `recommended_action`.

`changed_formal_checks` diffs indexed `lineage.formal_trust` fields: `lean_check_status`, `obligation_set_id`, `lean_check_result_id`, `lean_theorems`, `failed_lean_theorems`.

## Rendering benchmarks (evidence-layer gate)

Scientific Memory measures import/render/query quality under `benchmarks/rendering/`. The benchmark contract uses **17 interpretability sections** (`BENCHMARK_RENDERING_SECTIONS` in `sm_pipeline.benchmark.pcs_sections`); the portal adds **Assumptions** for full human-facing pages.

```bash
just pcs-benchmark-rendering-all OUT=benchmark_runs/pcs_rendering
python -m sm_pipeline.benchmark.pcs_rendering --cases benchmarks/rendering --out benchmark_runs/pcs_rendering
just validate-pcs-benchmark-output benchmark_runs/pcs_rendering
```

**pcs-bench canonical ingest:** `pcs_bench_ingest.v0.json` (`schema_version`: `v0`, `producer_id`: `scientific-memory`, `workflow_id`: `pcs.scientific_memory`). Embeds pcs-core `BenchmarkRun.v0`, `CoverageReport.v0`, `FailureLocalizationResult.v0`, and `ExplainQualityReport.v0` objects in `benchmark_runs`, `coverage_reports`, `failure_localization_reports`, and `explain_quality_reports` (plus empty `profile_coverage_reports`, `commands`, `logs`). Optional `artifact_refs` may point at on-disk companion reports. Hard gate: `--validate-pcs-core-output ../pcs-core` on the benchmark CLI or validate script (fails on any `PcsBenchIngest.v0` schema mismatch).

| Artifact | Role |
|----------|------|
| `pcs_bench_ingest.v0.json` | Canonical pcs-bench integration manifest |
| `benchmark_run.v0.json` | Aggregate run + structured `failure_summary` |
| `rendering_coverage_report.v0.json` | Per-case coverage mapped to pcs-core `explain_quality_section_id` values |
| `explain_quality_report.v0.json` | Bundle of `ExplainQualityReport.v0`-shaped per-case reports |
| `query_coverage_report.v0.json` | Query dispatch results |
| `failed_release_rendering_report.v0.json` | Failed-release evidence rendering |

`rendering_coverage_report.v0.json` uses pcs-core explain-quality sections: `provenance`, `hashes`, `handoffs`, `verification`, `formal_checks`, `limitations`, `lineage`, `repair_hints`.

Benchmark failures are typed (not collapsed): `import_failed`, `render_failed`, `query_failed`, `staleness_failed`, `comparison_failed`, `formal_failed`. Each event includes `responsible_component`, `repair_hint`, and `artifact_path`.

**External reviewer packet:** `benchmarks/rendering/external_reviewer_minimal/` (`suite_id`: `scientific-memory-external-reviewer-v0`). Run with `just pcs-benchmark-external-reviewer`.

Legacy alias: `pcs_bench_payload.json`. Suite registry: `benchmarks/pcs_bench/suite_registry.v0.json`. Full contract: [pcs-bench-ingest.md](pcs-bench-ingest.md). Package for upload: `python scripts/package_pcs_bench_bundle.py`. Thresholds: `benchmarks/rendering/baseline_thresholds.json` (10 cases). CI runs the external-reviewer packet via `scripts/run_pcs_rc_ci_gate.sh`.

**Success cases:** `labtrust_qc_release`, `tool_use_safety`, `computation_reproducibility`, `formal_trust_kernel`.

**Failed cases:** `rejected_certificate`, `stale_release`, `failed_lean_check`, `failed_pf_verification`, `missing_registry_metadata`, `result_hash_mismatch`.

**Query operations benchmarked:** `list_claims`, `show_claim`, `check_stale`, `by_certificate`, `by_source_commit`, `by_release`, `by_workflow`, `by_lean_theorem`, `by_dataset`, `by_result_hash`, `compare_releases`.

For computation releases, `changed_computation` may include: `dataset_changes`, `environment_changes`, `code_commit_changes`, `command_changes`, `result_hash_changes`, `witness_status_changes` (derived from indexed `lineage.computation` fields, not bundle rescans).

## Limitation notice

The canonical string is `sm_pipeline.pcs_import.artifact_normalizer.LIMITATION_NOTICE` (workflow-neutral wording). Workflow-specific notices from the release manifest are appended to `limitations[]`.

## Test IDs

- `pcs-claim-page`
- `pcs-section-workflow-profile`, `pcs-section-tool-use-trace`, `pcs-section-tool-use-certificate`
- `pcs-section-dataset-receipt`, `pcs-section-environment-receipt`, `pcs-section-computation-run-receipt`, `pcs-section-result-artifact`, `pcs-section-computation-witness`, `pcs-computation-witness-failures`
- `pcs-section-protocol-artifacts`, `pcs-protocol-artifact-<ArtifactType>`
- `pcs-section-formal-trust-kernel`, `pcs-formal-non-claims`, `pcs-formal-check-failures`
- `pcs-section-release-manifest`, `pcs-section-artifact-registry`, `pcs-section-lineage`, `pcs-section-staleness`
- See `tests/pcs/test_pcs_portal_contract.py` for the full list.

Python: `tests/pcs/`, portal scripts `verify-pcs-read-model.mjs` and `verify-pcs-phase2-read-model.mjs` (workflow-aware).

Golden fixtures:

- LabTrust: `tests/pcs/fixtures/labtrust-release/.phase2-read-model.json`
- Tool-use: `tests/pcs/fixtures/tool-use-release/.phase2-read-model.json`
- Computation (passed): `tests/pcs/fixtures/computation-release/.phase2-read-model.json`
- Computation (rejected witness): `tests/pcs/fixtures/computation-rejected-release/.phase2-read-model.json`
