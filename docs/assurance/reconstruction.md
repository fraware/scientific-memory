# Action-chain reconstruction

Export a portable assurance release, then re-import and validate it on a clean store.

## Export

```bash
uv run --project pipeline sm export-action-chain <action_id> --out bundle/
# or: just export-action-chain ACTION_ID=<action_id> OUT=bundle/
```

Produces `AssuranceReleaseManifest.v1.json`, artifact trees (`nodes/`, `edges/`, `outcomes/`, `calibrations/`, and related dirs), and `checksums.txt`.

## Clean reconstruction

```bash
uv run --project pipeline sm import-assurance-release bundle/
uv run --project pipeline sm validate-action-chain <action_id>
uv run --project pipeline sm metrics autonomous-science --out metrics.json
```

When the bundle includes PCS claim pointers, those claims must already be present in the target corpus (or include a nested PCS bundle and import it). Do not invent new PCS standards in this layer.

## Portal export

```bash
uv run --project pipeline sm export-assurance-portal-data
# or: just export-assurance-portal-data
pnpm --dir portal exec node scripts/verify-assurance-export.mjs
```

Writes `portal/.generated/assurance-export.json`. Public export redacts `internal` / `redacted` payloads unless `ASSURANCE_INCLUDE_INTERNAL=1`. The portal reads this file only; it does not scan `corpus/assurance/` at request time.
