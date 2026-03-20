"""Ingest commands: admit papers, build index, hash sources."""

from pathlib import Path

import typer

from sm_pipeline.ingest.admit_paper import admit_paper
from sm_pipeline.ingest.build_index import build_index
from sm_pipeline.ingest.hash_source import hash_all_sources, hash_source_for_paper
from sm_pipeline.ingest.intake_report import write_intake_report
from sm_pipeline.ingest.scaffold_gold import scaffold_gold

app = typer.Typer()


@app.command("add-paper")
def add_paper(paper_id: str) -> None:
    admit_paper(Path("."), paper_id)
    typer.echo(
        f"Paper {paper_id} admitted. Next: add claims (just extract-claims {paper_id}), "
        f"then run 'just scaffold-gold {paper_id}' to create benchmarks/gold for metrics."
    )


@app.command("batch-admit")
def batch_admit(
    csv_path: str = typer.Argument(..., help="CSV with columns paper_id, domain; optional title, year"),
) -> None:
    """Admit multiple papers from CSV; updates index. See docs/paper-intake.md."""
    from sm_pipeline.ingest.batch_admit import batch_admit_from_csv

    repo_root = Path(".").resolve()
    ids = batch_admit_from_csv(repo_root, Path(csv_path))
    typer.echo(f"Batch-admit processed {len(ids)} row(s): {ids}")


@app.command("build-index")
def build_index_cmd() -> None:
    """Rebuild corpus/index.json from admitted paper metadata."""
    out = build_index(Path("."))
    typer.echo(f"Index written to {out}")


@app.command("hash-source")
def hash_source_cmd(
    paper_id: str | None = typer.Option(
        None, "--paper-id", help="Paper ID (if omitted: all papers)"
    ),
) -> None:
    """Hash paper source file(s) and persist metadata.source.sha256."""
    repo_root = Path(".").resolve()
    if paper_id:
        digest = hash_source_for_paper(repo_root, paper_id)
        typer.echo(f"{paper_id}: {digest}")
        return
    results = hash_all_sources(repo_root)
    typer.echo(f"Hashed {len(results)} paper source file(s).")


@app.command("intake-report")
def intake_report(
    paper_id: str = typer.Option(..., "--paper-id", help="Paper ID"),
) -> None:
    """Write corpus/papers/<paper_id>/intake_report.json (optional; SPEC 8.1)."""
    repo_root = Path(".").resolve()
    out = write_intake_report(repo_root, paper_id)
    typer.echo(f"Intake report written to {out}")


@app.command("scaffold-gold")
def scaffold_gold_cmd(
    paper_id: str = typer.Option(..., "--paper-id", help="Paper ID"),
) -> None:
    """Scaffold benchmarks/gold/<paper_id>/ from corpus (claims, source_spans, assumptions). Run after add-paper or when adding gold for a new paper."""
    repo_root = Path(".").resolve()
    try:
        out = scaffold_gold(repo_root, paper_id)
        typer.echo(
            f"Gold scaffolded at {out['gold_dir']}: "
            f"{out['claims_count']} claims, {out['source_spans_count']} source_spans, {out['assumptions_count']} assumptions."
        )
    except FileNotFoundError as e:
        typer.echo(str(e), err=True)
        raise typer.Exit(1)
