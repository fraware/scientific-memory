# LabTrust release example

Canonical fixtures: `tests/pcs/fixtures/labtrust-release/`

```bash
just sync-labtrust-release
just pcs-import-release
```

Custom manifest:

```bash
just pcs-import-release RELEASE_MANIFEST=tests/pcs/fixtures/labtrust-release/ReleaseManifest.v0.json
```

Documentation: [docs/pcs/import-and-releases.md](../../docs/pcs/import-and-releases.md).
