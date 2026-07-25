"""Typer commands for the assurance / autonomous science layer."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer

from sm_pipeline.assurance.validate import AssuranceValidationError

app = typer.Typer(help="Assurance action-chain commands")


def _repo_root() -> Path:
    """Resolve repo root from cwd, or by walking up for schemas/assurance + corpus."""
    cwd = Path(".").resolve()
    if (cwd / "schemas" / "assurance").is_dir() and (cwd / "corpus").is_dir():
        return cwd
    for parent in cwd.parents:
        if (parent / "schemas" / "assurance").is_dir() and (parent / "corpus").is_dir():
            return parent
    return cwd


def _fail(exc: Exception) -> None:
    typer.echo(str(exc), err=True)
    raise typer.Exit(1)


@app.command("import-assurance-release")
def import_assurance_release_cmd(
    release: Path = typer.Argument(..., help="Path to assurance release directory"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Validate without writing"),
) -> None:
    """Validate and import an assurance release into corpus/assurance/actions/."""
    from sm_pipeline.assurance.import_ import import_assurance_release

    try:
        report = import_assurance_release(release, repo_root=_repo_root(), write=not dry_run)
    except AssuranceValidationError as exc:
        _fail(exc)
    typer.echo(
        f"Imported release {report.release_id} -> action {report.action_id} "
        f"(ok={report.ok}, files={len(report.written_paths)})"
    )


@app.command("validate-action-chain")
def validate_action_chain_cmd(
    action_id: str = typer.Argument(...),
    strict: bool = typer.Option(
        False,
        "--strict",
        help="Fail when structural gaps or delayed unresolved outcomes remain",
    ),
) -> None:
    """Validate append-only action-chain DAG for an action_id."""
    from sm_pipeline.assurance.graph import validate_chain
    import json

    try:
        result = validate_chain(_repo_root(), action_id, strict=strict)
    except AssuranceValidationError as exc:
        _fail(exc)
    typer.echo(json.dumps(result, indent=2))


@app.command("add-outcome")
def add_outcome_cmd(
    outcome: Path = typer.Argument(..., help="ScientificOutcomeRecord.v1 JSON path"),
) -> None:
    """Append an outcome record and outcome node (never rewrites claims)."""
    from sm_pipeline.assurance.mutations import add_outcome
    import json

    try:
        result = add_outcome(_repo_root(), outcome)
    except AssuranceValidationError as exc:
        _fail(exc)
    typer.echo(json.dumps(result, indent=2))


@app.command("add-calibration")
def add_calibration_cmd(
    calibration: Path = typer.Argument(..., help="ActionCalibrationRecord.v1 JSON path"),
) -> None:
    """Append a calibration record and calibration_update node."""
    from sm_pipeline.assurance.mutations import add_calibration
    import json

    try:
        result = add_calibration(_repo_root(), calibration)
    except AssuranceValidationError as exc:
        _fail(exc)
    typer.echo(json.dumps(result, indent=2))


@app.command("export-action-chain")
def export_action_chain_cmd(
    action_id: str = typer.Argument(...),
    out: Path = typer.Option(..., "--out", help="Output bundle directory"),
) -> None:
    """Export a portable assurance release for reconstruction."""
    from sm_pipeline.assurance.export import export_action_chain

    try:
        path = export_action_chain(_repo_root(), action_id, out)
    except AssuranceValidationError as exc:
        _fail(exc)
    typer.echo(f"Exported action chain to {path}")


@app.command("export-assurance-portal-data")
def export_assurance_portal_data_cmd() -> None:
    """Write portal/.generated/assurance-export.json (privacy-redacted by default)."""
    from sm_pipeline.assurance.export import write_assurance_portal_export

    path = write_assurance_portal_export(_repo_root())
    typer.echo(f"Wrote {path}")
