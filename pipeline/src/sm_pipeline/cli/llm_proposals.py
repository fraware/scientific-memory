"""LLM proposal generation and human-gated apply (Prime Intellect)."""

from __future__ import annotations

import difflib
import json
from pathlib import Path

import typer

from sm_pipeline.llm.apply_proposals import (
    apply_claim_proposals,
    apply_mapping_proposals,
    preview_apply_claim_proposals,
    preview_apply_mapping_proposals,
)
from sm_pipeline.llm.factory import get_llm_provider
from sm_pipeline.llm.lean_proposal_to_apply import write_apply_bundle_from_lean_proposals_file
from sm_pipeline.llm.proposals_claims import generate_llm_claim_proposals
from sm_pipeline.llm.proposals_mapping import generate_llm_mapping_proposals
from sm_pipeline.llm.proposals_lean import generate_llm_lean_proposals
from sm_pipeline.settings import LLMSettings, load_repo_env


def llm_claim_proposals(
    paper_id: str = typer.Option(..., "--paper-id"),
    output: str | None = typer.Option(
        None,
        "--output",
        "-o",
        help="Write JSON (default: corpus/papers/<paper_id>/llm_claim_proposals.json)",
    ),
    use_fake_provider: bool = typer.Option(
        False,
        "--use-fake-provider",
        help="Use stub provider (tests; no network)",
    ),
) -> None:
    """Suggest claim edits via Prime Intellect; writes a human-review-only proposal artifact."""
    repo_root = Path(".").resolve()
    load_repo_env(repo_root)
    settings = LLMSettings.from_env()
    provider = get_llm_provider(repo_root, use_fake=use_fake_provider)
    model = settings.model_claims
    data = generate_llm_claim_proposals(repo_root, paper_id, provider, model=model)
    out_path = (
        Path(output)
        if output
        else repo_root / "corpus" / "papers" / paper_id / "llm_claim_proposals.json"
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    typer.echo(
        f"Wrote {out_path} (verification_boundary=human_review_only; review then sm-pipeline llm-apply-claim-proposals)."
    )


def llm_mapping_proposals(
    paper_id: str = typer.Option(..., "--paper-id"),
    output: str | None = typer.Option(
        None,
        "--output",
        "-o",
        help="Default: corpus/papers/<paper_id>/llm_mapping_proposals.json",
    ),
    use_fake_provider: bool = typer.Option(False, "--use-fake-provider"),
) -> None:
    """Suggest mapping (claim_id -> Lean decl) entries; human-review-only artifact."""
    repo_root = Path(".").resolve()
    load_repo_env(repo_root)
    settings = LLMSettings.from_env()
    provider = get_llm_provider(repo_root, use_fake=use_fake_provider)
    model = settings.model_mapping
    data = generate_llm_mapping_proposals(repo_root, paper_id, provider, model=model)
    out_path = (
        Path(output)
        if output
        else repo_root / "corpus" / "papers" / paper_id / "llm_mapping_proposals.json"
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    typer.echo(
        f"Wrote {out_path} (verification_boundary=human_review_only; review then sm-pipeline llm-apply-mapping-proposals)."
    )


def llm_lean_proposals(
    paper_id: str = typer.Option(..., "--paper-id"),
    decl: str | None = typer.Option(
        None,
        "--decl",
        help="Optional short declaration name or claim focus hint",
    ),
    output: str | None = typer.Option(
        None,
        "--output",
        "-o",
        help="Default: corpus/papers/<paper_id>/llm_lean_proposals.json",
    ),
    use_fake_provider: bool = typer.Option(False, "--use-fake-provider"),
) -> None:
    """Suggest surgical Lean find/replace edits; writes human-review-only sidecar (no formal/ writes)."""
    repo_root = Path(".").resolve()
    load_repo_env(repo_root)
    settings = LLMSettings.from_env()
    provider = get_llm_provider(repo_root, use_fake=use_fake_provider)
    model = settings.model_lean
    data = generate_llm_lean_proposals(repo_root, paper_id, provider, model=model, decl=decl)
    out_path = (
        Path(output)
        if output
        else repo_root / "corpus" / "papers" / paper_id / "llm_lean_proposals.json"
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    typer.echo(
        f"Wrote {out_path} (human_review_only). Review, then "
        f"sm-pipeline llm-lean-proposals-to-apply-bundle ... and proof-repair-apply (dry-run first)."
    )


def llm_lean_proposals_to_apply_bundle(
    bundle: str = typer.Argument(..., help="Path to llm_lean_proposals.json"),
    proposal_id: str = typer.Option(..., "--proposal-id"),
    output: str = typer.Option(
        ...,
        "--output",
        "-o",
        help="Write proof_repair_apply_bundle JSON",
    ),
    review_record_path: str | None = typer.Option(
        None,
        "--review-record-path",
        help="Optional path recorded in bundle for audit",
    ),
) -> None:
    """Convert one reviewed Lean proposal into a proof-repair-apply bundle (still requires human-gated apply)."""
    p = write_apply_bundle_from_lean_proposals_file(
        Path(bundle),
        proposal_id,
        Path(output),
        review_record_path=review_record_path,
    )
    typer.echo(f"Wrote apply bundle {p} (use proof-repair-apply without --apply for preview).")


def llm_apply_claim_proposals(
    bundle: str = typer.Argument(..., help="Path to llm_claim_proposals.json"),
    apply_write: bool = typer.Option(False, "--apply", help="Write claims.json"),
    i_understand_human_reviewed: bool = typer.Option(
        False,
        "--i-understand-human-reviewed",
        help="Required with --apply",
    ),
) -> None:
    """Merge reviewed claim proposals into corpus claims.json (upsert by claim id)."""
    repo_root = Path(".").resolve()
    bundle_path = Path(bundle)
    if not apply_write:
        before, after = preview_apply_claim_proposals(repo_root, bundle_path)
        a = json.dumps(before, indent=2).splitlines(keepends=True)
        b = json.dumps(after, indent=2).splitlines(keepends=True)
        diff = difflib.unified_diff(
            a, b, fromfile="claims.json(before)", tofile="claims.json(after)"
        )
        typer.echo("".join(diff))
        typer.echo("Dry-run: no files written. Re-run with --apply --i-understand-human-reviewed.")
        return
    if not i_understand_human_reviewed:
        typer.echo("Refusing --apply without --i-understand-human-reviewed.", err=True)
        raise typer.Exit(1)
    out = apply_claim_proposals(repo_root, bundle_path)
    typer.echo(f"Updated {out}")


def llm_apply_mapping_proposals(
    bundle: str = typer.Argument(..., help="Path to llm_mapping_proposals.json"),
    apply_write: bool = typer.Option(False, "--apply"),
    i_understand_human_reviewed: bool = typer.Option(
        False,
        "--i-understand-human-reviewed",
    ),
) -> None:
    """Merge reviewed mapping proposals into corpus mapping.json."""
    repo_root = Path(".").resolve()
    bundle_path = Path(bundle)
    if not apply_write:
        before, after = preview_apply_mapping_proposals(repo_root, bundle_path)
        a = json.dumps(before, indent=2).splitlines(keepends=True)
        b = json.dumps(after, indent=2).splitlines(keepends=True)
        diff = difflib.unified_diff(
            a, b, fromfile="mapping.json(before)", tofile="mapping.json(after)"
        )
        typer.echo("".join(diff))
        typer.echo("Dry-run: no files written. Re-run with --apply --i-understand-human-reviewed.")
        return
    if not i_understand_human_reviewed:
        typer.echo("Refusing --apply without --i-understand-human-reviewed.", err=True)
        raise typer.Exit(1)
    out = apply_mapping_proposals(repo_root, bundle_path)
    typer.echo(f"Updated {out}")
