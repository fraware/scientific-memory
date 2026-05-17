# LabTrust release PCS fixture

Canonical input for Scientific Memory import/render tests.

**Source of truth:** `provability-fabric/tests/pcs/fixtures/labtrust-release/signed_science_claim_bundle.json`

Refresh:

```bash
just refresh-pcs-fixtures
```

Integrity check (CI / `just test-pcs`):

```bash
bash scripts/sm_python.sh scripts/verify_labtrust_release_fixture.py
```

Regenerate in Provability Fabric: `make freeze-pcs-labtrust-release`
