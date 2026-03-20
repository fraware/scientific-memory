"""Validate commands: schema validation, blueprint checks."""

import json
from pathlib import Path

import typer

from sm_pipeline.validate.schemas import validate_repo

app = typer.Typer()


@app.command("validate-all")
def validate_all(
    report_json: str | None = typer.Option(
        None,
        "--report-json",
        help="Write machine-readable gate report to this path (after successful validation)",
    ),
) -> None:
    repo_root = Path(".").resolve()
    if report_json:
        from sm_pipeline.validate.gate_engine import run_all_gates

        report = run_all_gates(repo_root)
        out_path = Path(report_json)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(report.to_json_dict(), indent=2), encoding="utf-8")
    else:
        validate_repo(repo_root)


@app.command("check-paper-blueprint")
def check_paper_blueprint_cmd(
    paper_id: str = typer.Argument(..., help="Paper ID to check"),
) -> None:
    """Report blueprint vs mapping.json mismatches (optional; SPEC 8.4)."""
    from sm_pipeline.validate.blueprint_check import check_paper_blueprint

    repo_root = Path(".").resolve()
    issues = check_paper_blueprint(repo_root, paper_id)
    if not issues:
        typer.echo(f"No blueprint or no issues for {paper_id}.")
        return
    for i in issues:
        if i.get("kind") == "missing":
            typer.echo(f"Missing in mapping: {i['claim_id']} -> {i.get('expected_decl', '?')}")
        elif i.get("kind") == "mismatch":
            typer.echo(
                f"Mismatch {i['claim_id']}: blueprint {i.get('expected_decl')} vs mapping {i.get('actual_decl')}"
            )
        else:
            typer.echo(i.get("message", str(i)))
