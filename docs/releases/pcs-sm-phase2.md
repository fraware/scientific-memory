# pcs-sm Phase 2 — release evidence interface

Scientific Memory is the **human-facing evidence layer** for PCS releases: it imports `ReleaseManifest.v0`, requires `ReleaseChainValidationResult.v0`, renders protocol metadata, tracks lineage across releases, and exposes query and comparison commands.

## Protocol artifacts (pcs-core canonical)

| Artifact | Role in Scientific Memory |
|----------|---------------------------|
| `ReleaseManifest.v0` | Primary import entry; artifact registry metadata |
| `ReleaseChainValidationResult.v0` | Required proof that the chain passed (`ProofChecked`) |
| `ArtifactRegistry.v0` | Loaded when present beside the manifest |
| `HandoffManifest.v0` | Handoff chain between producer repos |
| `WorkflowProfile.v0` | Resolved via `workflow_profile_id` on chain validation |
| `SignedScienceClaimBundle.v0` | Claim payload |
| `ToolUseTrace.v0` / `ToolUseCertificate.v0` | Rendered via dedicated portal views when listed in manifest |
| `DatasetReceipt.v0` / `EnvironmentReceipt.v0` / `ComputationRunReceipt.v0` / `ResultArtifact.v0` / `ComputationWitness.v0` | Computation reproducibility chain; promoted to top-level read-model fields |
| `ProofObligation.v0` / `LeanCheckResult.v0` | Formal Trust Kernel (Lean-checked PCS trust-envelope); required in strict release mode when `formal_trust_required` on the workflow profile |

## Import (primary)

```bash
just pcs-import-release
```

Default manifest: `tests/pcs/fixtures/labtrust-release/ReleaseManifest.v0.json` (run `just sync-labtrust-release` to refresh `examples/labtrust-release/` from pcs-core)

```bash
just pcs-import-release
just pcs-import-release RELEASE_MANIFEST=tests/pcs/fixtures/labtrust-release/ReleaseManifest.v0.json
```

### Tool-use safety release

```bash
just sync-tool-use-release
just pcs-import-tool-use-release
```

Fixture directory: `tests/pcs/fixtures/tool-use-release/` (`release_manifest.v0.json`, `ToolUseTrace.v0`, `ToolUseCertificate.v0`). Portal contract golden: `.phase2-read-model.json` in that directory.

```bash
just sync-tool-use-release
just pcs-import-tool-use-release
```

### Scientific computation reproducibility release

```bash
just sync-computation-release        # pcs-core sync or bootstrap fallback
just bootstrap-computation-release   # regenerate fixtures + .phase2-read-model.json
just verify-computation-release
just publish-computation-release-to-pcs-core
just pcs-import-computation-release
just pcs-import-computation-rejected-release   # rejected ComputationWitness (failure evidence)
```

Fixture directories:

- `tests/pcs/fixtures/computation-release/` — passed witness (`CertificateChecked` supplemental witness)
- `tests/pcs/fixtures/computation-rejected-release/` — `ComputationWitness.v0` status `Rejected` with violations
- Published copy: `examples/computation-release/`

Workflow profile: `scientific_computation.reproducibility_v0` (`schemas/pcs/workflow_profiles/` or pcs-core `examples/workflow_profiles/scientific_computation_reproducibility.valid.json`).

Requires in the release directory:

- `ReleaseManifest.v0.json`
- `ReleaseChainValidationResult.v0.json` (status `ProofChecked`, `workflow_profile_id` set)
- All manifest-listed artifacts including `signed_science_claim_bundle.json`
- `ArtifactRegistry.v0.json` when used by the release train

Python module:

```bash
python -m sm_pipeline.pcs_import.release_manifest_importer \
  --manifest tests/pcs/fixtures/labtrust-release/ReleaseManifest.v0.json \
  --release-mode \
  --render
```

Strict release mode: `strict=true`, `allow_legacy=false`, no fixture overlay on import reports.

## Corpus layout

```text
corpus/pcs/
  claims_index.json
  claims/<claim_id>/
    signed_bundle.json
    read_model.json
    import_manifest.json
    release_manifest.json
    release_chain_validation.json
    artifact_registry.json
    handoff_manifests.json
    workflow_profile.json
    lineage.json
    scientific_memory_import_report.json
portal/.generated/pcs-export.json
```

## Portal

`/pcs/claims/<id>` renders claim, workflow profile, release protocol sections, lineage, staleness, hashes, sources, reproduce/verify, and limitations. See [pcs-rendering-contract.md](../pcs-rendering-contract.md).

## Query commands (lineage / index)

All list commands read `corpus/pcs/claims_index.json` and per-claim `lineage.json` — they do not rescan raw bundles.

```bash
just pcs-list-claims
just pcs-show-claim claim_id=claim-pcs-qc-release-v0.1
just pcs-check-stale claim_id=claim-pcs-qc-release-v0.1
just pcs-refresh-stale
just pcs-list-stale-claims
just pcs-list-claims-by-certificate certificate_id=cert-trace-...
just pcs-list-claims-by-source-commit COMMIT=...
just pcs-list-claims-by-release release_id=release-pcs-v0.1-labtrust-qc
just pcs-list-claims-by-workflow workflow_id=labtrust.qc_release_v0.1
just pcs-list-claims-by-trace-hash trace_hash=sha256:...
just pcs-list-claims-with-formal-checks
just pcs-show-formal-checks CLAIM_ID=claim-pcs-qc-release-v0.1
just pcs-list-claims-by-lean-theorem THEOREM=PCS.CertificateMatchesRuntime
just pcs-list-claims-with-failed-formal-checks
just bootstrap-formal-trust-release RELEASE_DIR=tests/pcs/fixtures/labtrust-release
just pcs-list-claims-by-dataset DATASET_ID=dataset-demo-measurements-v0.1
just pcs-list-claims-by-code-commit COMMIT=4c5439ae358733f9a4c4a58e33fdaed1ab0d29de
just pcs-list-claims-by-result-hash HASH=sha256:...
just pcs-list-claims-by-environment ENVIRONMENT_ID=env-linux-py312-uv
just pcs-query-lineage
just pcs-query-lineage --stale-only
just pcs-query-lineage --claim-state stale
just pcs-query-lineage --workflow-id labtrust.qc_release_v0.1
```

## Compare releases

```bash
just pcs-compare-releases release-pcs-v0.1-labtrust-qc release-pcs-v0.2-example
```

JSON output: `changed_artifacts`, `changed_hashes`, `changed_source_commits`, `changed_certificates`, `changed_workflow_profile`, `changed_registry_checks`, `changed_computation`, `staleness_impact`, `recommended_action`.

`changed_computation` (when either release is a computation workflow) includes lineage-indexed diffs: dataset, environment, code commit, command, result hashes, witness status. Example:

```bash
just pcs-compare-releases release-pcs-v0.1-labtrust-qc release-pcs-v0.1-scientific-computation-reproducibility
```

Requires both `release_id` values in `claims_index.json` (from prior imports).

## Formal Trust Kernel (PCS Phase 5)

Scientific Memory imports `ProofObligation.v0` and `LeanCheckResult.v0` from `ReleaseManifest.v0` when the workflow profile sets `formal_trust_required`. The portal renders a **Formal Trust Kernel** section after verification and before release manifest metadata.

Cross-repo flow (pcs-core + PF + SM):

```bash
# pcs-core
pcs extract-proof-obligations --release examples/labtrust-release --out proof_obligation.v0.json
pcs lean-check --obligations proof_obligation.v0.json --out lean_check_result.v0.json

# PF (release mode)
pf verify science-claim science_claim_bundle.certified.json \
  --proof-obligations proof_obligation.v0.json \
  --lean-check-result lean_check_result.v0.json \
  --release-mode

# Scientific Memory
just pcs-import-release
just pcs-show-formal-checks CLAIM_ID=claim-pcs-qc-release-v0.1
```

Local fixture bootstrap (conformance / CI without a full Lean build):

```bash
just bootstrap-formal-trust-release
```

Formal artifacts are listed on `ReleaseManifest.v0` only (not `RELEASE_FIXTURE_MANIFEST.json`) so pcs-core atomic chain validation stays compatible.

## Staleness

Triggers: signed bundle hash, release manifest hash, certificate ID, trace hash, source commit, schema version, failed revalidation.

Claim states: `current`, `stale`, `superseded`, `withdrawn`, `revalidated`.

## Rendering benchmarks (evidence layer)

Scientific Memory is benchmarked as the human-facing PCS evidence layer: interpretability sections, query correctness, release comparison, and failed-release rendering.

```bash
just pcs-benchmark-rendering CASES=benchmarks/rendering/labtrust_qc_release OUT=benchmark_runs/labtrust_rendering
just pcs-benchmark-rendering-all OUT=benchmark_runs/pcs_rendering
python scripts/bootstrap_pcs_rendering_benchmarks.py   # regenerate expected_*.json after fixture changes
```

Cases: `labtrust_qc_release`, `tool_use_safety`, `computation_reproducibility`, `formal_trust_kernel`, plus `failed/*` (rejected certificate, stale, failed Lean/PF, missing registry metadata, result hash mismatch). External reviewer packet: `benchmarks/rendering/external_reviewer_minimal/` (5 cases).

**pcs-bench:** canonical file `pcs_bench_ingest.v0.json` (`schema_version`: `v0`, `producer_id`: `scientific-memory`, `workflow_id`: `pcs.scientific_memory`). Suite registry: `benchmarks/pcs_bench/suite_registry.v0.json`. See [pcs-bench-ingest.md](../pcs-bench-ingest.md).

```bash
just pcs-benchmark-external-reviewer
just validate-external-reviewer-benchmark
just validate-pcs-benchmark-output-pcs-core benchmark_runs/pcs_rendering ../pcs-core
python scripts/package_pcs_bench_bundle.py benchmark_runs/external_reviewer_minimal
uv run python scripts/sync_pcs_benchmark_schemas.py   # refresh SM mirrors from pcs-core
```

**Release-grade producer gate** (real `source_commit`, pcs-core schemas, coverage thresholds, full `artifact_refs`, dialect sidecars, `pcs-bench validate-ingest --release-grade`):

```bash
make pcs-bench-producer
# or (requires pcs-bench on PATH)
just pcs-bench-producer-gate
just pcs-bench-producer-gate-external   # 5-case external reviewer packet

sm-pipeline validate-pcs-bench-ingest \
  --input benchmark_runs/labtrust_rendering/pcs_bench_ingest.v0.json \
  --pcs-core ../pcs-core --release-grade

python scripts/package_pcs_bench_bundle.py benchmark_runs/external_reviewer_minimal \
  --validate-pcs-core-output ../pcs-core --release-grade
```

CI checks out `fraware/pcs-bench` when available and runs the producer gate without fixture fallback.

See [pcs-bench-ingest.md](../pcs-bench-ingest.md).

Typed benchmark failures: `import_failed`, `render_failed`, `query_failed`, `staleness_failed`, `comparison_failed`, `formal_failed`.

## CI gate

```bash
just pcs-rc-gate
just pcs-rc-gate-py
just pcs-phase2-gate
```

The RC gate includes the full PCS rendering benchmark suite (`benchmarks/rendering/`).

## Refresh fixtures

```bash
just refresh-pcs-release
uv run python scripts/sync_pcs_schemas.py
just sync-tool-use-release
just sync-computation-release
uv run python scripts/ensure_labtrust_phase2_fixtures.py
python scripts/verify_tool_use_release_fixture.py
python scripts/verify_computation_release_fixture.py
```

Portal contracts (no pnpm required):

```bash
node portal/scripts/verify-pcs-read-model.mjs
node portal/scripts/verify-pcs-phase2-read-model.mjs corpus/pcs/claims/claim-pcs-qc-release-v0.1/read_model.json
node portal/scripts/verify-pcs-phase2-read-model.mjs tests/pcs/fixtures/tool-use-release/.phase2-read-model.json
node portal/scripts/verify-pcs-phase2-read-model.mjs tests/pcs/fixtures/computation-release/.phase2-read-model.json
```
