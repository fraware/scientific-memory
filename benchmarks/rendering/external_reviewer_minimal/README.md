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
just pcs-benchmark-rendering CASES=benchmarks/rendering/external_reviewer_minimal OUT=benchmark_runs/external_reviewer_minimal
python scripts/validate_pcs_benchmark_output.py benchmark_runs/external_reviewer_minimal
```

Ingest manifest: `pcs_bench_ingest.v0.json` (`suite_id`: `scientific-memory-external-reviewer-v0`).

Regenerate expectations:

```bash
python scripts/bootstrap_pcs_rendering_benchmarks.py
```
