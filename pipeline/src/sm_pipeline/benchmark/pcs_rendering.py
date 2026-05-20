"""PCS rendering benchmark entry point (Scientific Memory evidence interface).

Run:
  python -m sm_pipeline.benchmark.pcs_rendering \\
    --cases benchmarks/rendering/labtrust_qc_release \\
    --out benchmark_runs/labtrust_rendering
"""

from sm_pipeline.benchmark.rendering import main

if __name__ == "__main__":
    raise SystemExit(main())
