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
| `ToolUseTrace.v0` / `ToolUseCertificate.v0` | Rendered via generic protocol artifact views when listed in manifest |

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
just pcs-query-lineage
just pcs-query-lineage --stale-only
just pcs-query-lineage --claim-state stale
just pcs-query-lineage --workflow-id labtrust.qc_release_v0.1
```

## Compare releases

```bash
just pcs-compare-releases release-pcs-v0.1-labtrust-qc release-pcs-v0.2-example
```

JSON output: `changed_artifacts`, `changed_hashes`, `changed_source_commits`, `changed_certificates`, `staleness_impact`, `recommended_action`.

Requires both `release_id` values in `claims_index.json` (from prior imports).

## Staleness

Triggers: signed bundle hash, release manifest hash, certificate ID, trace hash, source commit, schema version, failed revalidation.

Claim states: `current`, `stale`, `superseded`, `withdrawn`, `revalidated`.

## CI gate

```bash
just pcs-rc-gate
just pcs-rc-gate-py
just pcs-phase2-gate
```

## Refresh fixtures

```bash
just refresh-pcs-release
uv run python scripts/sync_pcs_schemas.py
just sync-tool-use-release
uv run python scripts/ensure_labtrust_phase2_fixtures.py
python scripts/verify_tool_use_release_fixture.py
```
