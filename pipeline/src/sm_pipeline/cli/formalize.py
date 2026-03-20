"""Formalize commands: mapping generation, formal scaffolding."""

from pathlib import Path

import typer

from sm_pipeline.formalize.mapping import generate_mapping
from sm_pipeline.formalize.scaffold import scaffold_formal as run_scaffold_formal

app = typer.Typer()


@app.command("scaffold-formal")
def scaffold_formal(
    paper_id: str = typer.Option(..., "--paper-id", help="Paper ID"),
) -> None:
    repo_root = Path(".").resolve()
    run_scaffold_formal(repo_root, paper_id)
    typer.echo(
        f"Mapping scaffolded for {paper_id}. Edit corpus/papers/{paper_id}/mapping.json to add claim_to_decl entries."
    )


@app.command("generate-mapping")
def generate_mapping_cmd(
    paper_id: str = typer.Option(..., "--paper-id", help="Paper ID"),
) -> None:
    """Generate mapping.json from claims and formal targets."""
    out = generate_mapping(Path("."), paper_id)
    typer.echo(f"Mapping generated for {paper_id}: {len(out.get('claim_to_decl', {}))} claim(s).")
