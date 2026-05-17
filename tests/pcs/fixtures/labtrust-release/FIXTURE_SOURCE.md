# LabTrust release PCS fixture

Canonical input for Scientific Memory import/render tests.

**Source of truth:** `pcs-core/examples/labtrust-release/` (PF-signed bundle with real `provability_fabric_commit` provenance; aligned on vendor)

Refresh:

```bash
just refresh-pcs-fixtures
```

Integrity check (CI / `just test-pcs`):

```bash
bash scripts/sm_python.sh scripts/verify_labtrust_release_fixture.py
```

Regenerate in Provability Fabric: `make freeze-pcs-labtrust-release`
