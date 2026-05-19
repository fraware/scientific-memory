"""CLI: PCS LabTrust bundle import, validate, and portal render."""

import json
import os
from pathlib import Path

import typer
from rich.console import Console

from sm_pipeline.pcs_import.claim_lineage import update_lineage_stale_flags
from sm_pipeline.pcs_import.claim_index import load_claims_index, query_claims_index
from sm_pipeline.pcs_import.claim_query import (
    list_claim_ids,
    list_claims_by_certificate,
    list_claims_by_code_commit,
    list_claims_by_dataset,
    list_claims_by_environment,
    list_claims_by_release_id,
    list_claims_by_result_hash,
    list_claims_by_source_commit,
    list_claims_by_trace_hash,
    list_claims_by_workflow,
    list_claims_by_lean_theorem,
    list_claims_with_failed_formal_checks,
    list_claims_with_formal_checks,
    list_stale_claims,
    show_formal_checks,
    load_claim_bundle,
    refresh_all_stale_flags,
)
from sm_pipeline.pcs_import.release_compare import compare_releases
from sm_pipeline.pcs_import.portal_export import write_pcs_portal_export
from sm_pipeline.pcs_import.lineage_ops import build_operational_staleness_view
from sm_pipeline.pcs_import.release_manifest_importer import import_release_manifest
from sm_pipeline.pcs_import.science_claim_bundle_importer import import_signed_bundle
from sm_pipeline.pcs_validate.validator import BundleValidationError, validate_signed_bundle

console = Console()


def _repo_root() -> Path:
    """Repo root: SCIENTIFIC_MEMORY_REPO_ROOT, else process cwd (matches other sm_pipeline CLIs)."""
    override = os.environ.get("SCIENTIFIC_MEMORY_REPO_ROOT", "").strip()
    if override:
        return Path(override).resolve()
    return Path.cwd().resolve()


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
            repo_root=_repo_root(),
            strict=strict,
            release_mode=release_mode,
            allow_legacy=allow_legacy,
        )
    except BundleValidationError as exc:
        console.print(f"[red]Import rejected:[/red] {exc}")
        raise typer.Exit(code=1) from exc

    write_pcs_portal_export(_repo_root())
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
            repo_root=_repo_root(),
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
            repo_root=_repo_root(),
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
    ids = list_claim_ids(_repo_root())
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
        data = load_claim_bundle(_repo_root(), claim_id)
    except FileNotFoundError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1) from exc
    typer.echo(json.dumps(data, indent=2, ensure_ascii=False))


def pcs_check_stale(
    claim_id: str = typer.Option(..., "--claim-id", help="PCS claim artifact id"),
    human: bool = typer.Option(
        False,
        "--human",
        help="Print human-readable status instead of JSON",
    ),
) -> None:
    """Check whether a claim is stale vs on-disk artifacts (JSON by default)."""
    import json

    from sm_pipeline.pcs_import.claim_query import claims_root

    claim_dir = claims_root(_repo_root()) / claim_id
    bundle_path = claim_dir / "signed_bundle.json"
    try:
        lineage = update_lineage_stale_flags(claim_dir, bundle_path=bundle_path)
    except FileNotFoundError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1) from exc

    manifest = None
    validation = None
    manifest_path = claim_dir / "release_manifest.json"
    validation_path = claim_dir / "release_chain_validation.json"
    if manifest_path.is_file():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    if validation_path.is_file():
        validation = json.loads(validation_path.read_text(encoding="utf-8-sig"))

    payload = build_operational_staleness_view(
        lineage,
        repo_root=_repo_root(),
        claim_id=claim_id,
        release_manifest=manifest if isinstance(manifest, dict) else None,
        validation=validation if isinstance(validation, dict) else None,
    )
    payload["claim_id"] = claim_id

    if human:
        state = payload.get("claim_state", "current")
        if payload["stale"]:
            console.print(
                f"[yellow]Stale[/yellow] {claim_id} ({state}): "
                f"{', '.join(payload['stale_reasons'])}",
            )
            console.print(f"[dim]repair:[/dim] {payload['repair_hint']}")
        else:
            console.print(f"[green]Fresh[/green] {claim_id} ({state})")
        return

    typer.echo(json.dumps(payload, indent=2, sort_keys=True))


def pcs_list_claims_by_certificate(
    certificate_id: str = typer.Option(..., "--certificate-id", help="Trace certificate id"),
) -> None:
    for claim_id in list_claims_by_certificate(_repo_root(), certificate_id):
        console.print(claim_id)


def pcs_list_claims_by_source_commit(
    commit: str = typer.Option(..., "--commit", help="40-char git commit hash"),
) -> None:
    for claim_id in list_claims_by_source_commit(_repo_root(), commit):
        console.print(claim_id)


def pcs_list_claims_by_release(
    release_id: str = typer.Option(..., "--release-id", help="PCS release_id"),
) -> None:
    for claim_id in list_claims_by_release_id(_repo_root(), release_id):
        console.print(claim_id)


def pcs_list_claims_by_workflow(
    workflow_id: str = typer.Option(..., "--workflow-id", help="WorkflowProfile workflow_id"),
) -> None:
    """List claim IDs for a workflow profile (from claims_index / lineage)."""
    for claim_id in list_claims_by_workflow(_repo_root(), workflow_id):
        console.print(claim_id)


def pcs_list_claims_by_dataset(
    dataset_id: str = typer.Option(..., "--dataset-id", help="DatasetReceipt dataset_id"),
) -> None:
    for claim_id in list_claims_by_dataset(_repo_root(), dataset_id):
        console.print(claim_id)


def pcs_list_claims_by_environment(
    environment_id: str = typer.Option(..., "--environment-id", help="EnvironmentReceipt environment_id"),
) -> None:
    for claim_id in list_claims_by_environment(_repo_root(), environment_id):
        console.print(claim_id)


def pcs_list_claims_by_code_commit(
    commit: str = typer.Option(..., "--commit", help="Computation run code_commit"),
) -> None:
    for claim_id in list_claims_by_code_commit(_repo_root(), commit):
        console.print(claim_id)


def pcs_list_claims_by_result_hash(
    result_hash: str = typer.Option(..., "--result-hash", help="ResultArtifact sha256 digest"),
) -> None:
    for claim_id in list_claims_by_result_hash(_repo_root(), result_hash):
        console.print(claim_id)


def pcs_compare_releases(
    old_release: str = typer.Option(..., "--old-release", help="Previous release_id"),
    new_release: str = typer.Option(..., "--new-release", help="Newer release_id"),
) -> None:
    """Compare two releases using lineage records (JSON to stdout)."""
    import json

    try:
        payload = compare_releases(
            _repo_root(),
            old_release_id=old_release,
            new_release_id=new_release,
        )
    except FileNotFoundError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1) from exc
    typer.echo(json.dumps(payload, indent=2, sort_keys=True))


def pcs_list_claims_by_trace_hash(
    trace_hash: str = typer.Option(..., "--trace-hash", help="Trace hash digest"),
) -> None:
    for claim_id in list_claims_by_trace_hash(_repo_root(), trace_hash):
        console.print(claim_id)


def pcs_list_claims_with_formal_checks() -> None:
    ids = list_claims_with_formal_checks(_repo_root())
    if not ids:
        console.print("[dim]No claims with formal trust checks.[/dim]")
        return
    for claim_id in ids:
        console.print(claim_id)


def pcs_show_formal_checks(
    claim_id: str = typer.Option(..., "--claim-id", help="PCS claim artifact id"),
) -> None:
    import json

    try:
        payload = show_formal_checks(_repo_root(), claim_id)
    except FileNotFoundError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1) from exc
    typer.echo(json.dumps(payload, indent=2, ensure_ascii=False))


def pcs_list_claims_by_lean_theorem(
    theorem: str = typer.Option(..., "--theorem", help="Lean theorem name (e.g. PCS.CertificateMatchesRuntime)"),
) -> None:
    for claim_id in list_claims_by_lean_theorem(_repo_root(), theorem):
        console.print(claim_id)


def pcs_list_claims_with_failed_formal_checks() -> None:
    ids = list_claims_with_failed_formal_checks(_repo_root())
    if not ids:
        console.print("[dim]No claims with failed formal trust checks.[/dim]")
        return
    for claim_id in ids:
        console.print(claim_id)


def pcs_list_stale_claims() -> None:
    """List claim IDs marked stale in lineage."""
    ids = list_stale_claims(_repo_root())
    if not ids:
        console.print("[dim]No stale PCS claims.[/dim]")
        return
    for claim_id in ids:
        console.print(claim_id)


def pcs_refresh_stale() -> None:
    """Recompute stale flags for all claims and refresh claims_index.json."""
    results = refresh_all_stale_flags(_repo_root())
    stale = sum(1 for row in results if row.get("lineage", {}).get("stale"))
    console.print(f"[green]Refreshed[/green] {len(results)} claim(s); {stale} stale")
    write_pcs_portal_export(_repo_root())


def pcs_query_lineage(
    release_id: str = typer.Option(None, "--release-id"),  # type: ignore[assignment]
    certificate_id: str = typer.Option(None, "--certificate-id"),  # type: ignore[assignment]
    trace_hash: str = typer.Option(None, "--trace-hash"),  # type: ignore[assignment]
    commit: str = typer.Option(None, "--commit"),  # type: ignore[assignment]
    claim_state: str = typer.Option(None, "--claim-state"),  # type: ignore[assignment]
    workflow_id: str = typer.Option(None, "--workflow-id"),  # type: ignore[assignment]
    dataset_id: str = typer.Option(None, "--dataset-id"),  # type: ignore[assignment]
    environment_id: str = typer.Option(None, "--environment-id"),  # type: ignore[assignment]
    result_hash: str = typer.Option(None, "--result-hash"),  # type: ignore[assignment]
    stale_only: bool = typer.Option(False, "--stale-only"),
) -> None:
    """Query corpus/pcs/claims_index.json (JSON lines to stdout)."""
    import json

    if not any(
        (
            release_id,
            certificate_id,
            trace_hash,
            commit,
            claim_state,
            workflow_id,
            dataset_id,
            environment_id,
            result_hash,
            stale_only,
        ),
    ):
        index = load_claims_index(_repo_root())
        typer.echo(json.dumps(index, indent=2))
        return
    matches = query_claims_index(
        _repo_root(),
        release_id=release_id,
        certificate_id=certificate_id,
        trace_hash=trace_hash,
        source_commit=commit,
        stale_only=stale_only,
        claim_state=claim_state,
        workflow_profile_id=workflow_id,
        dataset_id=dataset_id,
        environment_id=environment_id,
        code_commit=commit,
        result_hash=result_hash,
    )
    for entry in matches:
        typer.echo(json.dumps(entry, sort_keys=True))


def pcs_render_claim(
    claim_id: str = typer.Option(..., "--claim-id", help="PCS claim artifact id"),
) -> None:
    """Export portal PCS read model for rendering."""
    try:
        out = write_pcs_portal_export(_repo_root(), claim_id=claim_id)
    except FileNotFoundError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1) from exc
    console.print(f"[green]PCS portal export[/green] -> {out}")


def pcs_benchmark_rendering(
    cases: str = typer.Option(
        "benchmarks/rendering/labtrust_qc_release",
        "--cases",
        help="Benchmark case directory (single case or parent directory)",
    ),
    out: str = typer.Option(
        "",
        "--out",
        help="Output directory for rendering_benchmark_report.json",
    ),
    in_place: bool = typer.Option(
        False,
        "--in-place",
        help="Import into repo corpus instead of isolated workspace",
    ),
    check_regression: bool = typer.Option(
        True,
        "--check-regression/--no-check-regression",
        help="Enforce benchmarks/rendering/baseline_thresholds.json",
    ),
) -> None:
    """Run PCS import/render/query benchmarks (pcs-bench consumable report)."""
    from pathlib import Path

    from sm_pipeline.benchmark.rendering import (
        check_rendering_regression,
        export_pcs_bench_payload,
        run_rendering_benchmark,
    )

    repo = _repo_root()
    cases_path = Path(cases)
    if not cases_path.is_absolute():
        cases_path = repo / cases_path
    out_dir = Path(out) if out else repo / "benchmark_runs" / cases_path.name
    if out and not out_dir.is_absolute():
        out_dir = repo / out_dir

    report = run_rendering_benchmark(
        cases_path,
        repo_root=repo,
        out_dir=out_dir,
        isolated=not in_place,
    )
    bench_path = out_dir / "pcs_bench_payload.json"
    bench_path.write_text(
        json.dumps(export_pcs_bench_payload(report), indent=2) + "\n",
        encoding="utf-8",
    )
    report_path = report.get("report_path") or out_dir / "rendering_benchmark_report.json"
    if check_regression:
        ok, msg = check_rendering_regression(repo, report)
        if not ok and msg:
            console.print(f"[red]{msg}[/red]")
            raise typer.Exit(code=1)
    if report.get("passed"):
        console.print(f"[green]PCS rendering benchmark passed[/green] -> {report_path}")
        console.print(f"[dim]pcs-bench payload[/dim] -> {bench_path}")
    else:
        console.print(f"[red]PCS rendering benchmark failed[/red] -> {report_path}")
        for msg in report.get("failures") or []:
            console.print(f"  - {msg}")
        raise typer.Exit(code=1)
