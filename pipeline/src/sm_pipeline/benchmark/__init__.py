"""Scientific Memory benchmark runners (PCS rendering, corpus tasks)."""

from sm_pipeline.benchmark.pcs_sections import (
    BENCHMARK_RENDERING_SECTIONS,
    REQUIRED_INTERPRETABILITY_SECTIONS,
    evaluate_section_coverage,
)
from sm_pipeline.benchmark.report_builder import (
    PCS_BENCH_INGEST_FILENAME,
    V0_REPORT_FILENAMES,
    build_v0_reports,
    validate_benchmark_output_dir,
    validate_v0_reports,
    write_pcs_bench_artifacts,
    write_v0_reports,
)
from sm_pipeline.benchmark.rendering import (
    check_rendering_regression,
    discover_case_dirs,
    export_pcs_bench_payload,
    run_rendering_benchmark,
)

__all__ = [
    "BENCHMARK_RENDERING_SECTIONS",
    "PCS_BENCH_INGEST_FILENAME",
    "REQUIRED_INTERPRETABILITY_SECTIONS",
    "V0_REPORT_FILENAMES",
    "build_v0_reports",
    "check_rendering_regression",
    "discover_case_dirs",
    "evaluate_section_coverage",
    "export_pcs_bench_payload",
    "run_rendering_benchmark",
    "validate_benchmark_output_dir",
    "validate_v0_reports",
    "write_pcs_bench_artifacts",
    "write_v0_reports",
]
