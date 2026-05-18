# Tool-use safety conformance train (v0.1)

Protocol conformance fixtures for the `agent_tool_use.safety_v0` workflow profile. This is not a product demo; it exercises the shared PCS trust loop with `ToolUseTrace.v0` and `ToolUseCertificate.v0`.

## Validate

```bash
pcs validate examples/tool-use-release/tool_use_trace.valid.json
pcs validate examples/tool-use-release/tool_use_certificate.valid.json
pcs validate examples/tool-use-release/release_manifest.v0.json
pcs validate-release-chain examples/tool-use-release/
pcs conformance run --suite tool-use
pcs conformance run --suite multidomain
```

## Artifacts

| File | Type |
|------|------|
| `workflow_profile.v0.json` | `WorkflowProfile.v0` |
| `tool_use_trace.valid.json` | `ToolUseTrace.v0` |
| `tool_use_certificate.valid.json` | `ToolUseCertificate.v0` |
| `runtime_receipt.json` | `RuntimeReceipt.v0` |
| `handoff_to_certifyedge.json` | `HandoffManifest.v0` |
| `handoff_manifest.*.v0.json` | `HandoffManifest.v0` |
| `handoff_to_pf.json` | `HandoffManifest.v0` |
| `science_claim_bundle.certified.json` | `ScienceClaimBundle.v0` |
| `verification_result.json` | `VerificationResult.v0` |
| `signed_science_claim_bundle.json` | `SignedScienceClaimBundle.v0` |
| `scientific_memory_import_report.json` | SM import report (includes `workflow_profile_id`) |
| `release_manifest.v0.json` | `ReleaseManifest.v0` |
| `release_chain_validation_result.v0.json` | `ReleaseChainValidationResult.v0` |
| `RELEASE_FIXTURE_MANIFEST.json` | Legacy digest manifest for `pcs validate-release-chain` |

Invalid negative cases: `examples/tool-use-release-invalid/`.

Profile definition: `examples/workflow_profiles/agent_tool_use_safety.valid.json`.

Regenerate: `python scripts/materialize_tool_use_fixtures.py` or `just materialize-protocol`.
