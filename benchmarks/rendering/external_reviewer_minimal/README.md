# External reviewer rendering packet

Minimal PCS rendering benchmark for external reviewers and pcs-bench smoke ingest.

## Cases (5)

| Case | Intent |
|------|--------|
| `labtrust_valid` | Successful LabTrust QC release import and render |
| `failed_lean` | Formal trust kernel failed Lean check (evidence panel) |
| `stale_release` | Stale signed bundle / lineage drift |
| `result_hash_mismatch` | Computation witness result hash mismatch |
| `release_compare` | LabTrust vs computation release comparison |

## Run

```bash
just validate-external-reviewer-benchmark-full

# Or stepwise:
just pcs-benchmark-external-reviewer-pcs-core
just validate-external-reviewer-benchmark-pcs-core
```

Ingest: `pcs_bench_ingest.v0.json` (`suite_id`: `scientific-memory-external-reviewer-v0`) with embedded pcs-core v0 objects and `explain_quality_reports/` sidecars.

Regenerate expectations:

```bash
python scripts/bootstrap_pcs_rendering_benchmarks.py
```
