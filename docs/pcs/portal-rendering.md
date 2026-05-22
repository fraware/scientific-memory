# Portal rendering contract

Every PCS claim page at `/pcs/claims/<claim_id>` renders release evidence in a **domain-neutral** layout. Workflow-specific content comes from the read model and workflow profile, not hardcoded labels in shared components.

## Section order

| # | Section | Data source |
|---|---------|-------------|
| 1 | Claim | `read_model.claim` |
| 2 | Workflow Profile | `read_model.workflow_profile` |
| 3 | Assumptions | `read_model.assumption_set` |
| 4 | Runtime Evidence | `read_model.runtime_receipt` (hidden for computation domain) |
| 5 | Dataset Receipt | `read_model.dataset_receipt` |
| 6 | Environment Receipt | `read_model.environment_receipt` |
| 7 | Computation Run Receipt | `read_model.computation_run_receipt` |
| 8 | Result Artifact | `read_model.result_artifact` |
| 9 | Computation Witness | `read_model.computation_witness` |
| 10 | Tool-Use Trace | `read_model.tool_use_trace` |
| 11 | Tool-Use Certificate | `read_model.tool_use_certificate` |
| 12 | Temporal Certificate | `read_model.trace_certificate` |
| 13 | Verification Result | `read_model.verification_result` |
| 14 | Formal Trust Kernel | `read_model.formal_trust_kernel` |
| 15 | Release Manifest | `read_model.release_manifest` |
| 16 | Release Chain Validation | `read_model.release_chain_validation` |
| 17 | Artifact Registry | `read_model.artifact_registry` |
| 18 | Handoff Manifests | `read_model.handoff_manifests` |
| 19 | Protocol artifacts | `read_model.protocol_artifacts` (fallback) |
| 20 | Artifact Dependency Graph | `read_model.artifact_dependency_graph` |
| 21 | Lineage | `read_model.lineage` |
| 22 | Staleness | `read_model.staleness` |
| 23 | Artifact Hashes | `read_model.artifact_hashes`, `canonical_digests` |
| 24 | Source Repositories | `read_model.source_repositories` |
| 25 | Reproduce / Verify | `reproduce_commands`, `verify_commands` |
| 26 | Limitations | `limitation_notice`, `limitations` |

Sections 5–11 appear only when the workflow profile lists the corresponding artifact types.

## Read model fields

Release imports must populate:

- `workflow_id`, `domain`
- `runtime_artifact_types`, `certificate_artifact_types`
- `tool_use_trace`, `tool_use_certificate` when listed in the release manifest
- `formal_trust_kernel` when proof obligations and Lean check results are present
- Computation fields for `scientific_computation.reproducibility_v0`: dataset, environment, run receipt, result artifact, computation witness

## Computation workflow

When `domain === scientific_computation`:

| Section | Key fields |
|---------|------------|
| Dataset Receipt | ID, version, files, hashes, source URI, license |
| Environment Receipt | OS, architecture, runtimes, packages, container digest |
| Computation Run Receipt | command, code commit, receipt refs, exit code, stdout/stderr hashes |
| Result Artifact | kind, path, hash, size, media type |
| Computation Witness | status, hashes, checker, violations, repair hints |

A mandatory computation limitation notice states that the release verifies declared provenance and hash consistency only—not dataset fairness, model validity, or generalization.

**Rejected witnesses:** status `Rejected` renders a failure panel with per-violation checks, expected/actual hashes, responsible component, and repair hints.

## Formal trust kernel

When `formal_trust_kernel` is present:

| Subsection | Content |
|------------|---------|
| Summary | what was checked, overall status, Lean version, checker, theorems |
| Trust-boundary invariants | one per milestone obligation |
| Proof obligations | ID, predicate, Lean theorem, source artifacts |
| Lean check results | per-theorem result and status |
| Formal scope | what the Lean package covers |
| Formal non-claims | required disclaimers (see below) |
| Failed checks | theorem, obligation, repair hints when checks fail |

**Required formal non-claims**

- The Lean check attests the declared PCS trust-envelope invariant only.
- Scientific truth of the claim, unbiased datasets, and model validity remain outside the formal scope and must be stated explicitly in the UI.

Milestone theorems include `PCS.CertificateMatchesRuntime`, `PCS.VerificationAdmitsBundle`, `PCS.SignedBundleAdmissible`, `PCS.RejectedCertificateNotAdmissible`, `PCS.StaleCertificateNotAdmissible`.

Strict import rejects missing formal artifacts when required, non-`ProofChecked` Lean results, ID mismatches, or failed obligations.

## Artifact registry

Each row exposes artifact type, schema, producer, status, hash, source repo/commit, semantic checks, admission result, and consumer repos when those fields are present.

## Lineage and staleness

- `claim_state`: `current`, `stale`, `superseded`, `withdrawn`, `revalidated`
- Staleness: `stale_reasons`, `recommended_action`, `repair_hint`
- Lineage: `previous_release_id`, `newer_release_ids`, `changed_artifacts`, `changed_hashes`

## Release comparison

`pcs-compare-releases` reports artifact, hash, commit, certificate, workflow, registry, formal, and computation diffs plus `staleness_impact` and `recommended_action`.

## Limitation notice

Canonical text: `sm_pipeline.pcs_import.artifact_normalizer.LIMITATION_NOTICE`. Workflow-specific notices append to `limitations[]`.

## Tests and golden fixtures

Portal contract tests: `tests/pcs/test_pcs_portal_contract.py`.

Verification scripts:

- `portal/scripts/verify-pcs-read-model.mjs`
- `portal/scripts/verify-pcs-phase2-read-model.mjs`

Golden read models:

- `tests/pcs/fixtures/labtrust-release/.phase2-read-model.json`
- `tests/pcs/fixtures/tool-use-release/.phase2-read-model.json`
- `tests/pcs/fixtures/computation-release/.phase2-read-model.json`
- `tests/pcs/fixtures/computation-rejected-release/.phase2-read-model.json`

Benchmark coverage of portal sections: [benchmarks/rendering/README.md](../../benchmarks/rendering/README.md) and [bench-ingest-contract.md](bench-ingest-contract.md).
