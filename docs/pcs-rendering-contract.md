# PCS rendering contract

Every PCS claim page at `/pcs/claims/<claim_id>` must render release evidence in a **domain-neutral** layout. LabTrust QC and agent tool-use safety are workflow profiles; the portal does not hardcode LabTrust labels in shared components.

## Section order

| # | Section title | Component | Data source |
|---|---------------|-----------|-------------|
| 1 | Claim | `ClaimArtifactView` | `read_model.claim` |
| 2 | Workflow Profile | `WorkflowProfileView` | `read_model.workflow_profile` |
| 3 | Assumptions | `AssumptionSetView` | `read_model.assumption_set` |
| 4 | Runtime Evidence | `RuntimeReceiptView` | `read_model.runtime_receipt` |
| 5 | Tool-Use Trace | `ToolUseTraceView` | `read_model.tool_use_trace` (when present) |
| 6 | Tool-Use Certificate | `ToolUseCertificateView` | `read_model.tool_use_certificate` (when present) |
| 7 | Temporal Certificate | `TraceCertificateView` | `read_model.trace_certificate` (when profile lists `TraceCertificate.v0`) |
| 8 | Verification Result | `VerificationResultView` | `read_model.verification_result` |
| 9 | Release Manifest | `ReleaseManifestView` | `read_model.release_manifest` |
| 10 | Release Chain Validation | `ReleaseChainValidationView` | `read_model.release_chain_validation` |
| 11 | Artifact Registry | `ArtifactRegistryView` | `read_model.artifact_registry` |
| 12 | Handoff Manifests | `HandoffManifestView` | `read_model.handoff_manifests` |
| 13 | Protocol artifacts | `ProtocolArtifactsSection` | `read_model.protocol_artifacts` (generic fallback) |
| 14 | Artifact Dependency Graph | `ArtifactDependencyGraph` | `read_model.artifact_dependency_graph` |
| 15 | Lineage | `LineageView` | `read_model.lineage` |
| 16 | Staleness | `StalenessView` | `read_model.staleness` |
| 17 | Artifact Hashes | `ArtifactHashTable` | `read_model.artifact_hashes`, `canonical_digests` |
| 18 | Source Repositories | `SourceRepositories` | `read_model.source_repositories` |
| 19 | Reproduce / Verify | `ReplayCommand` | `reproduce_commands`, `verify_commands` |
| 20 | Limitations | `LimitationNotice` | `limitation_notice`, `limitations` |

## Workflow-aware read model (top level)

Release imports must populate (in addition to nested `workflow_profile`):

- `workflow_id`, `domain`
- `runtime_artifact_types`, `certificate_artifact_types`
- `tool_use_trace`, `tool_use_certificate` when listed in `ReleaseManifest.v0`

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

`pcs-compare-releases` reports: `changed_artifacts`, `changed_hashes`, `changed_source_commits`, `changed_certificates`, `changed_workflow_profile`, `changed_registry_checks`, `staleness_impact`, `recommended_action`.

## Limitation notice

The canonical string is `sm_pipeline.pcs_import.artifact_normalizer.LIMITATION_NOTICE` (workflow-neutral wording). Workflow-specific notices from the release manifest are appended to `limitations[]`.

## Test IDs

- `pcs-claim-page`
- `pcs-section-workflow-profile`, `pcs-section-tool-use-trace`, `pcs-section-tool-use-certificate`
- `pcs-section-protocol-artifacts`, `pcs-protocol-artifact-<ArtifactType>`
- `pcs-section-release-manifest`, `pcs-section-artifact-registry`, `pcs-section-lineage`, `pcs-section-staleness`
- See `tests/pcs/test_pcs_portal_contract.py` for the full list.

Python: `tests/pcs/`, portal scripts `verify-pcs-read-model.mjs` and `verify-pcs-phase2-read-model.mjs` (workflow-aware).

Golden fixtures:

- LabTrust: `tests/pcs/fixtures/labtrust-release/.phase2-read-model.json`
- Tool-use: `tests/pcs/fixtures/tool-use-release/.phase2-read-model.json`
