"""CLI submodules for sm_pipeline - main app composition."""

import typer

from sm_pipeline.cli import (
    agentic,
    extract,
    formalize,
    ingest,
    llm_proposals,
    metrics,
    pcs,
    publish,
    validate_cmd,
)

app = typer.Typer()

# Register all commands from submodules directly on main app (preserve existing command names)
# Ingest commands
app.command("add-paper")(ingest.add_paper)
app.command("batch-admit")(ingest.batch_admit)
app.command("build-index")(ingest.build_index_cmd)
app.command("hash-source")(ingest.hash_source_cmd)
app.command("intake-report")(ingest.intake_report)
app.command("scaffold-gold")(ingest.scaffold_gold_cmd)

# Extract commands
app.command("extract-claims")(extract.extract_claims)
app.command("extraction-report")(extract.extraction_report)
app.command("extract-from-source")(extract.extract_from_source)
app.command("normalize-paper")(extract.normalize_paper_cmd)
app.command("ambiguity-flags")(extract.ambiguity_flags)
app.command("check-tooling")(extract.check_tooling)

# Validate commands
app.command("validate-all")(validate_cmd.validate_all)
app.command("check-paper-blueprint")(validate_cmd.check_paper_blueprint_cmd)

# Formalize commands
app.command("scaffold-formal")(formalize.scaffold_formal)
app.command("generate-mapping")(formalize.generate_mapping_cmd)

# Publish commands
app.command("publish")(publish.publish)
app.command("export-portal-data")(publish.export_portal_data_cmd)
app.command("export-diff-baseline")(publish.export_diff_baseline_cmd)

# Metrics commands
app.command("metrics")(metrics.metrics_cmd)
app.command("benchmark")(metrics.benchmark)

# Agentic commands
app.command("proof-repair-proposals")(agentic.proof_repair_proposals)
app.command("proof-repair-apply")(agentic.proof_repair_apply)

# LLM proposal commands (Prime Intellect; suggest-only by default)
app.command("llm-claim-proposals")(llm_proposals.llm_claim_proposals)
app.command("llm-mapping-proposals")(llm_proposals.llm_mapping_proposals)
app.command("llm-apply-claim-proposals")(llm_proposals.llm_apply_claim_proposals)
app.command("llm-apply-mapping-proposals")(llm_proposals.llm_apply_mapping_proposals)
app.command("llm-lean-proposals")(llm_proposals.llm_lean_proposals)
app.command("llm-lean-proposals-to-apply-bundle")(llm_proposals.llm_lean_proposals_to_apply_bundle)

# PCS LabTrust import (v0.1)
app.command("pcs-import-bundle")(pcs.pcs_import_bundle)
app.command("pcs-import-release")(pcs.pcs_import_release)
app.command("pcs-list-claims")(pcs.pcs_list_claims)
app.command("pcs-show-claim")(pcs.pcs_show_claim)
app.command("pcs-check-stale")(pcs.pcs_check_stale)
app.command("pcs-list-claims-by-certificate")(pcs.pcs_list_claims_by_certificate)
app.command("pcs-list-claims-by-source-commit")(pcs.pcs_list_claims_by_source_commit)
app.command("pcs-list-claims-by-release")(pcs.pcs_list_claims_by_release)
app.command("pcs-list-claims-by-workflow")(pcs.pcs_list_claims_by_workflow)
app.command("pcs-list-claims-by-dataset")(pcs.pcs_list_claims_by_dataset)
app.command("pcs-list-claims-by-environment")(pcs.pcs_list_claims_by_environment)
app.command("pcs-list-claims-by-code-commit")(pcs.pcs_list_claims_by_code_commit)
app.command("pcs-list-claims-by-result-hash")(pcs.pcs_list_claims_by_result_hash)
app.command("pcs-compare-releases")(pcs.pcs_compare_releases)
app.command("pcs-list-claims-by-trace-hash")(pcs.pcs_list_claims_by_trace_hash)
app.command("pcs-list-claims-with-formal-checks")(pcs.pcs_list_claims_with_formal_checks)
app.command("pcs-show-formal-checks")(pcs.pcs_show_formal_checks)
app.command("pcs-list-claims-by-lean-theorem")(pcs.pcs_list_claims_by_lean_theorem)
app.command("pcs-list-claims-with-failed-formal-checks")(pcs.pcs_list_claims_with_failed_formal_checks)
app.command("pcs-list-stale-claims")(pcs.pcs_list_stale_claims)
app.command("pcs-refresh-stale")(pcs.pcs_refresh_stale)
app.command("pcs-query-lineage")(pcs.pcs_query_lineage)
app.command("pcs-validate-bundle")(pcs.pcs_validate_bundle)
app.command("pcs-render-claim")(pcs.pcs_render_claim)
app.command("pcs-benchmark-rendering")(pcs.pcs_benchmark_rendering)
app.command("validate-pcs-bench-ingest")(pcs.validate_pcs_bench_ingest)
