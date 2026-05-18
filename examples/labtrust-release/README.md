# LabTrust release example (Scientific Memory)

Canonical Phase 2 fixtures live under:

`tests/pcs/fixtures/labtrust-release/`

Populate from pcs-core (sibling checkout) then import:

```bash
just sync-labtrust-release
just pcs-import-release
```

Or import the test fixture tree directly:

```bash
just pcs-import-release RELEASE_MANIFEST=tests/pcs/fixtures/labtrust-release/ReleaseManifest.v0.json
```

The on-disk manifest artifact name is `ReleaseManifest.v0.json` (pcs-core convention).
