"""Publish commands: manifest generation, portal export, diff baselines."""

from pathlib import Path

import typer

from sm_pipeline.pipeline_orchestrator import run_export_portal_bundle, run_pipeline_for_paper
from sm_pipeline.models.stage_contracts import PipelineStage

app = typer.Typer()


@app.command("publish")
def publish(
    paper_id: str = typer.Option(..., "--paper-id", help="Paper ID"),
) -> None:
    report = run_pipeline_for_paper(Path(".").resolve(), paper_id, stages=[PipelineStage.publication])
    for o in report.outcomes:
        typer.echo(f"[{o.stage.value}] {o.message}")


@app.command("export-portal-data")
def export_portal_data_cmd() -> None:
    """Export canonical portal data bundle from corpus artifacts."""
    o = run_export_portal_bundle(Path(".").resolve())
    path = (o.details or {}).get("path", "")
    typer.echo(f"Portal export written to {path}")


@app.command("export-diff-baseline")
def export_diff_baseline_cmd(
    snapshot_at: str | None = typer.Option(
        None, "--snapshot-at", help="ISO timestamp for baseline; default now"
    ),
    baseline_id: str = typer.Option(
        "last-release",
        "--baseline-id",
        help="Baseline file id under corpus/snapshots (without .json)",
    ),
    title: str | None = typer.Option(
        None, "--title", help="Optional baseline title shown on portal diff page"
    ),
    narrative: str | None = typer.Option(
        None, "--narrative", help="Optional narrative summary shown on portal diff page"
    ),
) -> None:
    """Export current corpus state to corpus/snapshots/<baseline-id>.json for the Diff page."""
    from sm_pipeline.publish.diff_baseline import export_diff_baseline

    repo_root = Path(".").resolve()
    out = export_diff_baseline(
        repo_root,
        snapshot_at=snapshot_at,
        baseline_id=baseline_id,
        title=title,
        narrative=narrative,
    )
    typer.echo(f"Diff baseline written to {out}")
