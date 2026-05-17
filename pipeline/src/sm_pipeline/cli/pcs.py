"""CLI: PCS LabTrust bundle import, validate, and portal render."""

from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console

from sm_pipeline.pcs_import.portal_export import write_pcs_portal_export
from sm_pipeline.pcs_import.science_claim_bundle_importer import import_signed_bundle
from sm_pipeline.pcs_validate.validator import BundleValidationError, validate_signed_bundle

console = Console()
_REPO_ROOT = Path(__file__).resolve().parents[4]


def pcs_import_bundle(
    bundle: Path = typer.Option(..., "--bundle", "-b", help="Signed bundle JSON path"),
    strict: bool = typer.Option(True, help="Reject invalid bundles"),
    release_mode: bool = typer.Option(
        False,
        "--release-mode",
        help="Strict PCS Core release import; pin report from sibling fixture when present",
    ),
    allow_legacy: bool = typer.Option(
        False,
        "--allow-legacy",
        help="Accept legacy LabTrust portal signed bundles in strict mode",
    ),
) -> None:
    """Import a signed LabTrust PCS bundle into corpus/pcs/claims/."""
    try:
        result = import_signed_bundle(
            bundle,
            repo_root=_REPO_ROOT,
            strict=strict,
            release_mode=release_mode,
            allow_legacy=allow_legacy,
        )
    except BundleValidationError as exc:
        console.print(f"[red]Import rejected:[/red] {exc}")
        raise typer.Exit(code=1) from exc

    write_pcs_portal_export(_REPO_ROOT)
    console.print(f"[green]Imported claim[/green] {result.claim_id}")
    console.print(f"  -> {result.import_dir}")
    for w in result.warnings:
        console.print(f"[yellow]Warning:[/yellow] {w}")


def pcs_validate_bundle(
    bundle: Path = typer.Option(..., "--bundle", "-b", help="Signed bundle JSON path"),
    allow_legacy: bool = typer.Option(
        False,
        "--allow-legacy",
        help="Accept legacy LabTrust portal signed bundles in strict mode",
    ),
) -> None:
    """Validate a signed bundle without importing."""
    import json

    from sm_pipeline.pcs_import.bundle_utils import bundle_for_validation
    from sm_pipeline.pcs_validate.bundle_detection import detect_bundle_shape

    raw = json.loads(bundle.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        console.print("[red]Bundle must be a JSON object[/red]")
        raise typer.Exit(code=1)
    shape = detect_bundle_shape(raw)
    console.print(f"[dim]bundle_shape:[/dim] {shape}")
    try:
        warnings = validate_signed_bundle(
            bundle_for_validation(raw),
            repo_root=_REPO_ROOT,
            strict=True,
            allow_legacy=allow_legacy,
        )
    except BundleValidationError as exc:
        console.print(f"[red]Invalid bundle:[/red] {exc}")
        raise typer.Exit(code=1) from exc

    console.print("[green]Bundle is valid[/green]")
    for w in warnings:
        console.print(f"[yellow]Warning:[/yellow] {w}")


def pcs_render_claim(
    claim_id: str = typer.Option(..., "--claim-id", help="PCS claim artifact id"),
) -> None:
    """Export portal PCS read model for rendering."""
    try:
        out = write_pcs_portal_export(_REPO_ROOT, claim_id=claim_id)
    except FileNotFoundError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1) from exc
    console.print(f"[green]PCS portal export[/green] -> {out}")
