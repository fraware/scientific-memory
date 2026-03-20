"""CLI submodules for sm_pipeline - main app composition."""

import typer

from sm_pipeline.cli import agentic, extract, formalize, ingest, metrics, publish, validate_cmd

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
