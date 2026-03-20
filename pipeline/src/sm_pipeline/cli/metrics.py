"""Metrics commands: compute corpus metrics, run benchmarks."""

from pathlib import Path

import typer

app = typer.Typer()


@app.command("metrics")
def metrics_cmd(
    median_intake: bool = typer.Option(
        False,
        "--median-intake-time",
        help="Median time from intake to first artifact",
    ),
    dependency: bool = typer.Option(
        False,
        "--dependency",
        help="Dependency reuse ratio and fan-in/fan-out",
    ),
    symbol_conflict: bool = typer.Option(
        False,
        "--symbol-conflict",
        help="Symbol normalization conflict rate",
    ),
    proof_completion: bool = typer.Option(
        False,
        "--proof-completion",
        help="Proof completion rate from manifests",
    ),
    normalization_report: bool = typer.Option(
        False,
        "--normalization-report",
        help="Cross-paper duplicate normalized_name (8.3)",
    ),
    axiom_count: bool = typer.Option(
        False,
        "--axiom-count",
        help="Axiom/sorry count from Lean source (formal/)",
    ),
    research_value: bool = typer.Option(
        False,
        "--research-value",
        help="Research-value: reusable foundation, cross-paper reuse",
    ),
    source_span_alignment: bool = typer.Option(
        False,
        "--source-span-alignment",
        help="Source-span alignment error rate vs benchmarks/gold source_spans.json",
    ),
    normalization_visibility: bool = typer.Option(
        False,
        "--normalization-visibility",
        help="8.3: symbols with role_unclear, claims without linked_assumptions",
    ),
    assumption_suggestions: bool = typer.Option(
        False,
        "--assumption-suggestions",
        help="8.3: suggest candidate assumptions for claims with none (text overlap)",
    ),
    dimension_visibility: bool = typer.Option(
        False,
        "--dimension-visibility",
        help="8.3: symbols with vs without dimensional_metadata",
    ),
    dimension_suggestions: bool = typer.Option(
        False,
        "--dimension-suggestions",
        help="8.3: heuristic suggested dimensional_metadata for symbols (human triage)",
    ),
    normalization_policy: bool = typer.Option(
        False,
        "--normalization-policy",
        help="8.3: run waiver-backed normalization policy checks (warn-only report)",
    ),
    reviewer_report: bool = typer.Option(
        False,
        "--reviewer-report",
        help="Reviewer lifecycle report: claims by status, disputed with/without notes",
    ),
    output: str | None = typer.Option(None, "--output", "-o", help="Write JSON report to path"),
) -> None:
    """Compute metrics from corpus (SPEC 12). Default: run all; use flags to run specific metrics."""
    from sm_pipeline.metrics import (
        compute_median_intake_time,
        compute_dependency_metrics,
        compute_symbol_conflict_rates,
        compute_cross_paper_normalized_duplicates,
        compute_proof_completion,
        compute_axiom_count,
        compute_research_value_metrics,
        compute_source_span_alignment,
        compute_normalization_visibility,
        compute_assumption_suggestions,
        compute_dimension_visibility,
        compute_dimension_suggestions,
        compute_reviewer_status_metrics,
    )

    repo_root = Path(".").resolve()
    run_all = not (
        median_intake
        or dependency
        or symbol_conflict
        or proof_completion
        or normalization_report
        or axiom_count
        or research_value
        or source_span_alignment
        or normalization_visibility
        or assumption_suggestions
        or dimension_visibility
        or dimension_suggestions
        or normalization_policy
        or reviewer_report
    )
    report: dict = {}
    if median_intake or run_all:
        result = compute_median_intake_time(repo_root)
        report["median_intake_time"] = result
        if result:
            typer.echo(
                f"Median intake to first artifact: {result['median_seconds']}s "
                f"(n={result['count']})"
            )
        else:
            typer.echo(
                "Median intake: no papers with both intake_report.created_at "
                "and metadata.first_artifact_at"
            )
    if dependency or run_all:
        result = compute_dependency_metrics(repo_root)
        report["dependency"] = result
        typer.echo(
            f"Dependency reuse ratio: {result['dependency_reuse_ratio']}; edges: {result['total_edges']}"
        )
    if symbol_conflict or run_all:
        result = compute_symbol_conflict_rates(repo_root)
        report["symbol_conflict"] = result
        agg = result["aggregate"]
        typer.echo(
            f"Symbol conflict rate: {agg['symbol_conflict_rate']:.4f}; "
            f"with flags: {agg['total_with_ambiguity_flags']}"
        )
    if proof_completion or run_all:
        result = compute_proof_completion(repo_root)
        report["proof_completion"] = result
        tgt = result.get("milestone_3_target", 40)
        cur = result.get("milestone_3_current", 0)
        typer.echo(
            f"Proof completion: {result['proof_completion_rate']:.4f} "
            f"({result['total_machine_checked']}/{result['total_mapped_claims']} mapped); "
            f"Milestone 3: {cur}/{tgt} machine-checked"
        )
    if normalization_report or run_all:
        result = compute_cross_paper_normalized_duplicates(repo_root)
        report["cross_paper_normalized_duplicates"] = result
        typer.echo(f"Cross-paper duplicate normalized_name count: {result['count']}")
    if axiom_count or run_all:
        result = compute_axiom_count(repo_root)
        report["axiom_count"] = result
        typer.echo(
            f"Axiom count: {result['total_axiom_count']}; "
            f"sorry count: {result['total_sorry_count']} "
            f"({result['files_scanned']} files)"
        )
        if result.get("by_paper"):
            for pid, pdata in sorted(result["by_paper"].items()):
                typer.echo(
                    f"  {pid}: axiom={pdata['axiom_count']} sorry={pdata['sorry_count']} "
                    f"({len(pdata['files'])} file(s))"
                )
    if research_value or run_all:
        result = compute_research_value_metrics(repo_root)
        report["research_value"] = result
        typer.echo(
            f"Research-value: reusable foundation {result['reusable_foundation_count']}; "
            f"literature errors (ADR placeholder) {result['literature_errors_count']}; "
            f"disputed w/ formal targets {result.get('disputed_claims_with_formal_targets', 0)}"
        )
    if source_span_alignment or run_all:
        result = compute_source_span_alignment(repo_root)
        report["source_span_alignment"] = result
        if result.get("total_compared", 0) > 0:
            typer.echo(
                f"Source-span alignment: {result['alignment_error_count']}/"
                f"{result['total_compared']} errors (rate={result['alignment_error_rate']})"
            )
        else:
            typer.echo(
                "Source-span alignment: no reference data (benchmarks/gold/*/source_spans.json)"
            )
    if normalization_visibility or run_all:
        result = compute_normalization_visibility(repo_root)
        report["normalization_visibility"] = result
        typer.echo(
            f"8.3 visibility: {result['symbols_with_role_unclear_count']} symbols "
            f"with role_unclear; {result['claims_without_linked_assumptions_count']} "
            "claims without linked_assumptions (papers with assumptions)"
        )
    if assumption_suggestions or run_all:
        result = compute_assumption_suggestions(repo_root)
        report["assumption_suggestions"] = result
        typer.echo(
            f"8.3 assumption suggestions: {result['suggestion_count']} claim(s) "
            "with candidates (review and link manually)"
        )
    if dimension_visibility or run_all:
        result = compute_dimension_visibility(repo_root)
        report["dimension_visibility"] = result
        typer.echo(
            f"8.3 dimension visibility: {result['with_count']} symbols with "
            f"dimensional_metadata; {result['without_count']} without"
        )
    if dimension_suggestions or run_all:
        result = compute_dimension_suggestions(repo_root)
        report["dimension_suggestions"] = result
        typer.echo(
            f"8.3 dimension suggestions: {result['suggestion_count']} symbol(s) "
            "(heuristic; human triage only, no auto-edit)"
        )
    if normalization_policy or run_all:
        from sm_pipeline.validate.normalization_policy import run_policy_checks

        result = run_policy_checks(repo_root)
        report["normalization_policy"] = result
        if result.get("warnings"):
            for w in result["warnings"]:
                typer.echo(f"Normalization policy (warn): {w}", err=True)
        elif result.get("policy_loaded"):
            typer.echo("Normalization policy: no violations")
        else:
            typer.echo("Normalization policy: no policy file (benchmarks/normalization_policy.json)")
    if reviewer_report or run_all:
        from sm_pipeline.validate.reviewer import compute_reviewer_report

        result = compute_reviewer_report(repo_root)
        report["reviewer_report"] = result
        disputed_wo = len(result.get("disputed_without_notes") or [])
        invalid = len(result.get("invalid_status_claims") or [])
        if disputed_wo or invalid:
            typer.echo(
                f"Reviewer report: {disputed_wo} disputed without notes, {invalid} invalid status(es)"
            )
        else:
            typer.echo("Reviewer report: claims by status; no disputed-without-notes or invalid status")
        card_result = compute_reviewer_status_metrics(repo_root)
        report["reviewer_status"] = card_result
        typer.echo(
            "Reviewer status (theorem cards): "
            f"{card_result['total_cards']} cards; "
            f"blocked={card_result['by_status']['blocked']}, "
            f"unreviewed={card_result['by_status']['unreviewed']}, "
            f"reviewed={card_result['by_status']['reviewed']}, "
            f"accepted={card_result['by_status']['accepted']}"
        )
        mc_unrev = int(card_result.get("machine_checked_but_unreviewed") or 0)
        if mc_unrev:
            typer.echo(
                f"Reviewer lifecycle (warn): {mc_unrev} machine_checked card(s) still "
                "unreviewed; see docs/contributor-playbook.md#theorem-card-reviewer-lifecycle-policy",
                err=True,
            )
    if output:
        import json as _json

        out_path = Path(output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(_json.dumps(report, indent=2), encoding="utf-8")
        typer.echo(f"Report written to {out_path}")


@app.command("benchmark")
def benchmark(
    output: str | None = typer.Option(None, "--output", "-o", help="Write report JSON to path"),
    check_regression: bool = typer.Option(
        True,
        "--check-regression/--no-check-regression",
        help="Fail if metrics regress below baseline",
    ),
) -> None:
    from sm_pipeline.benchmark_runner import check_regression as run_check_regression
    from sm_pipeline.benchmark_runner import main as run_benchmarks

    repo_root = Path(".").resolve()
    report_path = Path(output) if output else repo_root / "benchmarks" / "reports" / "latest.json"
    report = run_benchmarks(repo_root, report_path)
    typer.echo(f"Benchmark report written to {report_path}")
    if check_regression:
        passed, msg = run_check_regression(repo_root, report)
        if not passed:
            typer.echo(msg, err=True)
            raise typer.Exit(1)
