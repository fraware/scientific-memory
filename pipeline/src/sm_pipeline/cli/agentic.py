"""Agentic commands: proof repair proposals and application."""

from pathlib import Path

import typer

app = typer.Typer()


@app.command("proof-repair-proposals")
def proof_repair_proposals(
    paper_id: str | None = typer.Option(None, "--paper-id", help="Limit to one paper"),
    output: str | None = typer.Option(
        None, "--output", "-o", help="Write proposal artifact to path"
    ),
) -> None:
    """Generate proof-repair proposals (human_review_only). Never auto-applied; write to --output for review."""
    from sm_pipeline.agentic.proof_repair import generate_repair_proposals
    import json as _json

    repo_root = Path(".").resolve()
    result = generate_repair_proposals(repo_root, paper_id)
    if output:
        out_path = Path(output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(_json.dumps(result, indent=2), encoding="utf-8")
        typer.echo(
            f"Proposals written to {out_path} (verification_boundary=human_review_only; do not auto-apply)."
        )
    else:
        typer.echo(_json.dumps(result, indent=2))
    typer.echo(f"Proposal count: {len(result.get('proposals') or [])}")


@app.command("proof-repair-apply")
def proof_repair_apply(
    proposal: str = typer.Argument(..., help="Path to proof_repair_apply_bundle.json"),
    apply_write: bool = typer.Option(
        False,
        "--apply",
        help="Write files (default is dry-run only)",
    ),
    i_understand_human_reviewed: bool = typer.Option(
        False,
        "--i-understand-human-reviewed",
        help="Required with --apply; confirms a human reviewed the patch bundle",
    ),
    review_record: str | None = typer.Option(
        None,
        "--review-record",
        help="Optional path to review record JSON (must match bundle.review_record_path if set)",
    ),
) -> None:
    """Apply human-reviewed find/replace patches under formal/ only. Never run from CI."""
    from sm_pipeline.agentic.proof_repair_apply import (
        apply_bundle,
        load_apply_bundle,
        preview_apply,
    )

    repo_root = Path(".").resolve()
    bundle = load_apply_bundle(Path(proposal), repo_root)
    rr = bundle.get("review_record_path")
    if rr and review_record:
        b = Path(rr).as_posix()
        a = Path(review_record).as_posix()
        if a != b:
            typer.echo(
                f"review_record path {review_record!r} does not match bundle {rr!r}",
                err=True,
            )
            raise typer.Exit(1)
    if not apply_write:
        rows = preview_apply(repo_root, bundle)
        for rel, before, after in rows:
            typer.echo(f"--- {rel}")
            typer.echo(f"- find (truncated): {before!r}")
            typer.echo(f"- replace (truncated): {after!r}")
        typer.echo(
            f"Dry-run: {len(rows)} replacement(s). "
            "Re-run with --apply --i-understand-human-reviewed to write."
        )
        return
    if not i_understand_human_reviewed:
        typer.echo("Refusing --apply without --i-understand-human-reviewed.", err=True)
        raise typer.Exit(1)
    modified = apply_bundle(repo_root, bundle)
    typer.echo(f"Applied patches to: {modified}")
