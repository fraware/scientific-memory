"""Scientific Memory benchmark runners (PCS rendering, corpus tasks)."""

from sm_pipeline.benchmark.bench_registry import load_suite_registry, validate_suite_id
from sm_pipeline.benchmark.failure_taxonomy import FAILURE_KINDS, failure_event, summarize_failure_kinds
from sm_pipeline.benchmark.pcs_core_coverage import (
    EXPLAIN_QUALITY_SECTION_IDS,
    build_explain_quality_report,
    suite_id_for_cases_path,
)
from sm_pipeline.benchmark.pcs_core_ingest import (
    SM_COVERAGE_METRICS,
    build_artifact_refs_for_ingest,
    build_embedded_pcs_bench_ingest,
    validate_embedded_ingest_contract,
)
from sm_pipeline.benchmark.pcs_sections import (
    BENCHMARK_RENDERING_SECTIONS,
    REQUIRED_INTERPRETABILITY_SECTIONS,
    evaluate_section_coverage,
)
from sm_pipeline.benchmark.report_builder import (
    EXPLAIN_QUALITY_REPORT_FILENAME,
    PCS_BENCH_INGEST_FILENAME,
    V0_REPORT_FILENAMES,
    build_pcs_bench_ingest,
    build_v0_reports,
    resolve_source_commit,
    validate_benchmark_output_dir,
    validate_v0_reports,
    write_pcs_bench_artifacts,
    write_v0_reports,
)
from sm_pipeline.benchmark.pcs_core_benchmark_validate import (
    resolve_pcs_core_from_env,
    resolve_pcs_core_root,
    validate_benchmark_artifacts_with_pcs_core,
    validate_benchmark_reports_dual,
)
from sm_pipeline.benchmark.rendering import (
    check_rendering_regression,
    discover_case_dirs,
    export_pcs_bench_payload,
    run_rendering_benchmark,
)

__all__ = [
    "load_suite_registry",
    "validate_suite_id",
    "BENCHMARK_RENDERING_SECTIONS",
    "EXPLAIN_QUALITY_REPORT_FILENAME",
    "EXPLAIN_QUALITY_SECTION_IDS",
    "FAILURE_KINDS",
    "PCS_BENCH_INGEST_FILENAME",
    "REQUIRED_INTERPRETABILITY_SECTIONS",
    "V0_REPORT_FILENAMES",
    "SM_COVERAGE_METRICS",
    "build_artifact_refs_for_ingest",
    "build_embedded_pcs_bench_ingest",
    "build_explain_quality_report",
    "build_pcs_bench_ingest",
    "validate_embedded_ingest_contract",
    "build_v0_reports",
    "check_rendering_regression",
    "discover_case_dirs",
    "evaluate_section_coverage",
    "export_pcs_bench_payload",
    "failure_event",
    "resolve_source_commit",
    "run_rendering_benchmark",
    "suite_id_for_cases_path",
    "summarize_failure_kinds",
    "resolve_pcs_core_from_env",
    "resolve_pcs_core_root",
    "validate_benchmark_artifacts_with_pcs_core",
    "validate_benchmark_output_dir",
    "validate_benchmark_reports_dual",
    "validate_v0_reports",
    "write_pcs_bench_artifacts",
    "write_v0_reports",
]
