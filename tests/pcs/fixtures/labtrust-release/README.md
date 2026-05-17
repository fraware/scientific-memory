# LabTrust v0.1 release fixtures

This directory contains **generated PCS v0.1 release-candidate artifacts** (release evidence only). Files must be produced by the end-to-end LabTrust → CertifyEdge → Provability Fabric → Scientific Memory chain, then imported with `pcs_core.release_fixtures --write`, which aligns embedded `source_commit` values to the five-repo manifest and re-signs PCS digests. **Placeholder commits are prohibited** for final release tags.

Schema conformance fixtures live in [`../labtrust/`](../labtrust/) and must not be used as release evidence.

## Regeneration

1. Run the clean-checkout chain from a sibling [LabTrust-Gym](https://github.com/fraware/LabTrust-Gym) checkout:

   ```bash
   export PCS_DETERMINISTIC=1
   bash examples/pcs_qc_release/scripts/run_pcs_v01_clean_chain.sh
   ```

2. Import chain outputs into pcs-core (from pcs-core repo root):

   ```bash
   export PCS_CHAIN_WORK=../LabTrust-Gym   # or absolute path to chain workdir
   just generate-labtrust-release-fixtures
   ```

   Optional commit overrides (defaults: `git rev-parse HEAD` in each sibling repo):

   ```bash
   export LABTRUST_GYM_COMMIT=<40-hex>
   export CERTIFYEDGE_COMMIT=<40-hex>
   export PROVABILITY_FABRIC_COMMIT=<40-hex>
   export SCIENTIFIC_MEMORY_COMMIT=<40-hex>
   ```

`RELEASE_FIXTURE_MANIFEST.json` records five repository commits and SHA-256 digests of every file in this directory.

## Validation

```bash
pcs validate-release-manifest examples/labtrust-release/RELEASE_FIXTURE_MANIFEST.json
# or
just validate-labtrust-release-fixtures
```

PCS artifacts must pass `pcs validate`. `trace.json` and `scientific_memory_import_report.json` are pipeline exports recorded in the manifest but are not PCS artifact schemas.

## Authority

Only this directory may be used as **PCS v0.1 release evidence**. See [docs/labtrust-v0.1-profile.md](../../docs/labtrust-v0.1-profile.md).
