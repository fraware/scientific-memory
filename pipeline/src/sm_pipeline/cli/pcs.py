"""CLI: PCS LabTrust bundle import, validate, and portal render."""

from pathlib import Path

import typer
from rich.console import Console

from sm_pipeline.pcs_import.claim_lineage import update_lineage_stale_flags
from sm_pipeline.pcs_import.claim_index import load_claims_index, query_claims_index
from sm_pipeline.pcs_import.claim_query import (
    list_claim_ids,
    list_claims_by_certificate,
    list_claims_by_release_id,
    list_claims_by_source_commit,
    list_claims_by_trace_hash,
    list_stale_claims,
    load_claim_bundle,
    refresh_all_stale_flags,
)
from sm_pipeline.pcs_import.portal_export import write_pcs_portal_export
from sm_pipeline.pcs_import.release_manifest_importer import import_release_manifest
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


def pcs_import_release(
    release_manifest: Path = typer.Option(
        ...,
        "--release-manifest",
        "-m",
        help="ReleaseManifest.v0 JSON path",
    ),
) -> None:
    """Import a PCS release from ReleaseManifest.v0 (strict release mode)."""
    try:
        result = import_release_manifest(
            release_manifest,
            repo_root=_REPO_ROOT,
            write=True,
            render=True,
        )
    except BundleValidationError as exc:
        console.print(f"[red]Release import rejected:[/red] {exc}")
        raise typer.Exit(code=1) from exc

    console.print(f"[green]Imported release claim[/green] {result.claim_id}")
    console.print(f"  -> {result.import_dir}")
    for warning in result.warnings:
        console.print(f"[yellow]Warning:[/yellow] {warning}")


def pcs_list_claims() -> None:
    """List imported PCS claim IDs."""
    ids = list_claim_ids(_REPO_ROOT)
    if not ids:
        console.print("[dim]No PCS claims imported.[/dim]")
        return
    for claim_id in ids:
        console.print(claim_id)


def pcs_show_claim(
    claim_id: str = typer.Option(..., "--claim-id", help="PCS claim artifact id"),
) -> None:
    """Show claim read model summary."""
    import json

    try:
        data = load_claim_bundle(_REPO_ROOT, claim_id)
    except FileNotFoundError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1) from exc
    console.print(json.dumps(data, indent=2))


def pcs_check_stale(
    claim_id: str = typer.Option(..., "--claim-id", help="PCS claim artifact id"),
) -> None:
    """Check whether a claim is stale vs on-disk artifacts."""
    from sm_pipeline.pcs_import.claim_query import claims_root

    claim_dir = claims_root(_REPO_ROOT) / claim_id
    bundle_path = claim_dir / "signed_bundle.json"
    try:
        lineage = update_lineage_stale_flags(claim_dir, bundle_path=bundle_path)
    except FileNotFoundError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1) from exc
    if lineage.get("stale"):
        console.print(f"[yellow]Stale[/yellow] {claim_id}: {', '.join(lineage.get('stale_reasons') or [])}")
    else:
        console.print(f"[green]Fresh[/green] {claim_id}")


def pcs_list_claims_by_certificate(
    certificate_id: str = typer.Option(..., "--certificate-id", help="Trace certificate id"),
) -> None:
    for claim_id in list_claims_by_certificate(_REPO_ROOT, certificate_id):
        console.print(claim_id)


def pcs_list_claims_by_source_commit(
    commit: str = typer.Option(..., "--commit", help="40-char git commit hash"),
) -> None:
    for claim_id in list_claims_by_source_commit(_REPO_ROOT, commit):
        console.print(claim_id)


def pcs_list_claims_by_release(
    release_id: str = typer.Option(..., "--release-id", help="PCS release_id"),
) -> None:
    for claim_id in list_claims_by_release_id(_REPO_ROOT, release_id):
        console.print(claim_id)


def pcs_list_claims_by_trace_hash(
    trace_hash: str = typer.Option(..., "--trace-hash", help="Trace hash digest"),
) -> None:
    for claim_id in list_claims_by_trace_hash(_REPO_ROOT, trace_hash):
        console.print(claim_id)


def pcs_list_stale_claims() -> None:
    """List claim IDs marked stale in lineage."""
    ids = list_stale_claims(_REPO_ROOT)
    if not ids:
        console.print("[dim]No stale PCS claims.[/dim]")
        return
    for claim_id in ids:
        console.print(claim_id)


def pcs_refresh_stale() -> None:
    """Recompute stale flags for all claims and refresh claims_index.json."""
    results = refresh_all_stale_flags(_REPO_ROOT)
    stale = sum(1 for row in results if row.get("lineage", {}).get("stale"))
    console.print(f"[green]Refreshed[/green] {len(results)} claim(s); {stale} stale")
    write_pcs_portal_export(_REPO_ROOT)


def pcs_query_lineage(
    release_id: str = typer.Option(None, "--release-id"),  # type: ignore[assignment]
    certificate_id: str = typer.Option(None, "--certificate-id"),  # type: ignore[assignment]
    trace_hash: str = typer.Option(None, "--trace-hash"),  # type: ignore[assignment]
    commit: str = typer.Option(None, "--commit"),  # type: ignore[assignment]
    stale_only: bool = typer.Option(False, "--stale-only"),
) -> None:
    """Query corpus/pcs/claims_index.json (JSON lines to stdout)."""
    import json

    if not any((release_id, certificate_id, trace_hash, commit, stale_only)):
        index = load_claims_index(_REPO_ROOT)
        console.print(json.dumps(index, indent=2))
        return
    matches = query_claims_index(
        _REPO_ROOT,
        release_id=release_id,
        certificate_id=certificate_id,
        trace_hash=trace_hash,
        source_commit=commit,
        stale_only=stale_only,
    )
    for entry in matches:
        console.print(json.dumps(entry, sort_keys=True))


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
