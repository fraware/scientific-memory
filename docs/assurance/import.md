# Assurance release import

Validate and import a portable assurance release into `corpus/assurance/actions/<action_id>/`. Import is fail-closed: identity conflicts, digest mismatches, non-admissible lifecycle, ambiguous dual IDs, missing required PCS pointers, and incomplete checksum coverage are rejected.

## Layout

```
release/
  AssuranceReleaseManifest.v1.json
  refs/                 # optional external artifact snapshots
  pcs/                  # optional nested PCS bundle (mode=bundle)
  execution/
  outcomes/
  calibrations/
  nodes/
  edges/
  checksums.txt
```

## Commands

```bash
# From repo root (sm aliases sm-pipeline)
uv run --project pipeline sm import-assurance-release path/to/release/
uv run --project pipeline sm import-assurance-release path/to/release/ --dry-run
uv run --project pipeline sm validate-action-chain <action_id>
```

Just recipes:

```bash
just import-assurance-release RELEASE=path/to/release
just validate-action-chain ACTION_ID=action-demo
```

## Nested PCS

| `pcs.mode` | Behavior |
|------------|----------|
| `bundle` | Nested signed bundle import via the existing PCS importer |
| `claim_pointers` | Claim ID + digest must already exist under `corpus/pcs/claims/` |
| `none` | Allowed with a warning; no PCS evidence attached |

Assurance import does not invent PCS standards or rewrite existing PCS claim digests.
