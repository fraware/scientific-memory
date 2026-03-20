"""Extract commands: claims, assumptions, symbols, normalization."""

from pathlib import Path

import typer

from sm_pipeline.extract.ambiguity import apply_ambiguity_suggestions, suggest_ambiguity_flags
from sm_pipeline.extract.claims import extract_claims as run_extract_claims
from sm_pipeline.extract.normalize import normalize_paper
from sm_pipeline.extract.report import write_extraction_run

app = typer.Typer()


@app.command("extract-claims")
def extract_claims(
    paper_id: str = typer.Option(..., "--paper-id", help="Paper ID"),
) -> None:
    repo_root = Path(".").resolve()
    run_extract_claims(repo_root, paper_id)
    typer.echo(
        f"Extraction complete for {paper_id}. Edit corpus/papers/{paper_id}/claims.json (and assumptions, symbols) as needed."
    )


@app.command("extraction-report")
def extraction_report(
    paper_id: str = typer.Option(..., "--paper-id", help="Paper ID"),
) -> None:
    """Write corpus/papers/<paper_id>/extraction_run.json (optional artifact; SPEC 8.2)."""
    repo_root = Path(".").resolve()
    out = write_extraction_run(repo_root, paper_id)
    typer.echo(f"Extraction run record written to {out}")


@app.command("extract-from-source")
def extract_from_source(
    paper_id: str = typer.Argument(..., help="Paper ID"),
) -> None:
    """Optional: run pandoc on source/main.tex and write suggested_claims.json for review."""
    from sm_pipeline.extract.pandoc_source import extract_from_source as run_extract_from_source

    repo_root = Path(".").resolve()
    out = run_extract_from_source(repo_root, paper_id)
    if out:
        typer.echo(f"Suggested claims written to {out}. Review and merge into claims.json.")
    else:
        typer.echo("No output: install pandoc and add corpus/papers/<paper_id>/source/main.tex")


@app.command("normalize-paper")
def normalize_paper_cmd(
    paper_id: str = typer.Option(..., "--paper-id", help="Paper ID"),
) -> None:
    """Run normalization transformations on symbols/assumptions/claim links."""
    out = normalize_paper(Path("."), paper_id)
    typer.echo(
        f"Normalized {paper_id}: {out['symbol_count']} symbols, "
        f"{out['assumption_count']} assumptions, duplicates={out['duplicate_normalized_name_count']}"
    )


@app.command("ambiguity-flags")
def ambiguity_flags(
    paper_id: str = typer.Option(..., "--paper-id", help="Paper ID"),
    apply: bool = typer.Option(False, "--apply", help="Write suggested flags to symbols.json"),
) -> None:
    """Suggest or apply ambiguity_flags on symbols (e.g. overloaded_symbol, unit_unclear)."""
    repo_root = Path(".").resolve()
    paper_dir = repo_root / "corpus" / "papers" / paper_id
    if not paper_dir.is_dir():
        typer.echo(f"Paper directory not found: {paper_dir}", err=True)
        raise typer.Exit(1)
    if apply:
        applied = apply_ambiguity_suggestions(paper_dir, write_back=True)
        typer.echo(f"Applied ambiguity_flags to {len(applied)} symbol(s) in {paper_id}")
    else:
        suggestions = suggest_ambiguity_flags(paper_dir)
        for s in suggestions:
            typer.echo(f"  {s.get('id', s['index'])}: suggest {s['suggested_flags']}")
        typer.echo(
            f"Suggested flags for {len(suggestions)} symbol(s). Use --apply to write to symbols.json."
        )


@app.command("check-tooling")
def check_tooling() -> None:
    """Report optional tooling availability (e.g. pandoc). Non-gate."""
    from sm_pipeline.extract.pandoc_source import check_pandoc_available

    pandoc = check_pandoc_available()
    if pandoc["available"]:
        typer.echo(f"pandoc: available ({pandoc.get('version') or 'unknown'})")
    else:
        typer.echo("pandoc: not found (optional; for extract-from-source)")
