# LabTrust release fixture

Canonical input for Scientific Memory import and render tests.

**Source of truth:** `pcs-core/examples/labtrust-release/` (signed bundle with Provability Fabric provenance).

Refresh from pcs-core:

```bash
just refresh-pcs-release
```

Integrity check:

```bash
bash scripts/sm_python.sh scripts/verify_labtrust_release_fixture.py
```

Regenerate in Provability Fabric: `make freeze-pcs-labtrust-release`
