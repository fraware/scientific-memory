# External reviewer rendering packet

Five benchmark cases for external review and pcs-bench smoke ingest.

| Case | Intent |
|------|--------|
| `labtrust_valid` | Successful LabTrust QC release import and render |
| `failed_lean` | Formal trust kernel failed Lean check |
| `stale_release` | Stale signed bundle / lineage drift |
| `result_hash_mismatch` | Computation witness result hash mismatch |
| `release_compare` | LabTrust vs computation release comparison |

## Run

```bash
make pcs-bench-producer-external

# Or stepwise:
just pcs-benchmark-external-reviewer-pcs-core
just validate-external-reviewer-benchmark-pcs-core
just validate-external-reviewer-benchmark-full
```

Output: `benchmark_runs/external_reviewer_minimal/pcs_bench_ingest.v0.json` (`suite_id`: `scientific-memory-external-reviewer-v0`).

Regenerate expectations after fixture changes:

```bash
python scripts/bootstrap_pcs_rendering_benchmarks.py
```

Full PCS docs: [docs/pcs/README.md](../../../docs/pcs/README.md).
