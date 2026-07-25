"""Autonomous-science metrics with visible denominators and exclusions."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from sm_pipeline.assurance.graph import actions_root, list_gaps, load_chain
from sm_pipeline.assurance.models import MetricExclusion, MetricSlice, utc_now_iso
from sm_pipeline.assurance.validate import AssuranceValidationError


METRIC_KEYS = (
    "evidence_sufficiency",
    "decision_and_review_agreement",
    "outcome_resolution",
    "calibration_error",
    "replication_rate",
    "adverse_event_frequency",
    "time_to_outcome",
    "information_gain",
    "cost",
    "missingness",
    "reconstruction_completeness",
)


def _slice(
    definition_id: str,
    *,
    numerator: float,
    population: list[str],
    included: list[str],
    exclusions: list[MetricExclusion],
    notes: str | None = None,
) -> MetricSlice:
    """Build a metric slice; fail closed if included + excluded != population."""
    excluded_ids = [e.id for e in exclusions]
    classified = sorted(set(included) | set(excluded_ids))
    pop_sorted = sorted(population)
    if classified != pop_sorted:
        overlap = set(included) & set(excluded_ids)
        missing = set(pop_sorted) - set(classified)
        extra = set(classified) - set(pop_sorted)
        raise AssuranceValidationError(
            f"{definition_id}: included+excluded must partition population "
            f"(overlap={sorted(overlap)} missing={sorted(missing)} extra={sorted(extra)})"
        )
    return MetricSlice(
        definition_id=definition_id,
        numerator=numerator,
        denominator=float(len(population)),
        included_ids=list(included),
        exclusions=exclusions,
        notes=notes,
    )


def compute_autonomous_science_metrics(repo_root: Path) -> dict[str, Any]:
    root = actions_root(repo_root)
    action_ids = sorted(p.name for p in root.iterdir() if p.is_dir()) if root.is_dir() else []
    chains = {aid: load_chain(repo_root, aid) for aid in action_ids}

    included_es: list[str] = []
    excl_es: list[MetricExclusion] = []
    for aid, chain in chains.items():
        classes = {n.get("node_class") for n in chain.nodes.values()}
        if "evidence" in classes and "claim" in classes:
            included_es.append(aid)
        else:
            excl_es.append(MetricExclusion(id=aid, reason="missing evidence or claim node"))
    evidence_sufficiency = _slice(
        "assurance.evidence_sufficiency.v1",
        numerator=float(len(included_es)),
        population=action_ids,
        included=included_es,
        exclusions=excl_es,
    )

    included_dr: list[str] = []
    excl_dr: list[MetricExclusion] = []
    num_dr = 0.0
    for aid, chain in chains.items():
        classes = {n.get("node_class") for n in chain.nodes.values()}
        if "review" not in classes or "grant" not in classes:
            excl_dr.append(MetricExclusion(id=aid, reason="missing review or grant"))
            continue
        included_dr.append(aid)
        num_dr += 1.0
    decision_review = _slice(
        "assurance.decision_and_review_agreement.v1",
        numerator=num_dr,
        population=action_ids,
        included=included_dr,
        exclusions=excl_dr,
    )

    included_or: list[str] = []
    excl_or: list[MetricExclusion] = []
    num_or = 0.0
    for aid, chain in chains.items():
        if not chain.outcomes:
            excl_or.append(MetricExclusion(id=aid, reason="no outcome records"))
            continue
        included_or.append(aid)
        resolved = all(
            o.get("delayed_result_status") != "delayed_unresolved" for o in chain.outcomes.values()
        )
        if resolved:
            num_or += 1.0
    outcome_resolution = _slice(
        "assurance.outcome_resolution.v1",
        numerator=num_or,
        population=action_ids,
        included=included_or,
        exclusions=excl_or,
    )

    included_ce: list[str] = []
    excl_ce: list[MetricExclusion] = []
    errors: list[float] = []
    for aid, chain in chains.items():
        aggregable = [
            c
            for c in chain.calibrations.values()
            if c.get("aggregation_eligibility")
            and (c.get("prediction_presence") or {}).get("success")
            and c.get("predicted_success") is not None
            and c.get("realized_success") is not None
        ]
        if not aggregable:
            excl_ce.append(MetricExclusion(id=aid, reason="no aggregable success predictions"))
            continue
        included_ce.append(aid)
        for c in aggregable:
            pred = float(c["predicted_success"])
            realized = 1.0 if c["realized_success"] else 0.0
            errors.append(abs(pred - realized))
    calibration_error = _slice(
        "assurance.calibration_error.v1",
        numerator=float(sum(errors) / len(errors)) if errors else 0.0,
        population=action_ids,
        included=included_ce,
        exclusions=excl_ce,
        notes="numerator is mean absolute calibration error over aggregable records",
    )

    included_rr: list[str] = []
    excl_rr: list[MetricExclusion] = []
    num_rr = 0.0
    for aid, chain in chains.items():
        if not chain.outcomes:
            excl_rr.append(MetricExclusion(id=aid, reason="no outcomes"))
            continue
        included_rr.append(aid)
        if any(o.get("replication_status") == "replicated" for o in chain.outcomes.values()) or any(
            n.get("node_class") == "replication" for n in chain.nodes.values()
        ):
            num_rr += 1.0
    replication_rate = _slice(
        "assurance.replication_rate.v1",
        numerator=num_rr,
        population=action_ids,
        included=included_rr,
        exclusions=excl_rr,
    )

    included_ae: list[str] = []
    excl_ae: list[MetricExclusion] = []
    num_ae = 0.0
    for aid, chain in chains.items():
        if not chain.outcomes:
            excl_ae.append(MetricExclusion(id=aid, reason="no outcomes"))
            continue
        included_ae.append(aid)
        events = sum(len(o.get("adverse_events") or []) for o in chain.outcomes.values())
        if events > 0:
            num_ae += 1.0
    adverse = _slice(
        "assurance.adverse_event_frequency.v1",
        numerator=num_ae,
        population=action_ids,
        included=included_ae,
        exclusions=excl_ae,
    )

    included_tt: list[str] = []
    excl_tt: list[MetricExclusion] = []
    times: list[float] = []
    for aid, chain in chains.items():
        with_time = [
            c for c in chain.calibrations.values() if c.get("realized_time") is not None
        ]
        if not with_time:
            excl_tt.append(MetricExclusion(id=aid, reason="no realized_time"))
            continue
        included_tt.append(aid)
        times.extend(float(c["realized_time"]) for c in with_time)
    time_to_outcome = _slice(
        "assurance.time_to_outcome.v1",
        numerator=float(sum(times) / len(times)) if times else 0.0,
        population=action_ids,
        included=included_tt,
        exclusions=excl_tt,
        notes="numerator is mean realized_time seconds",
    )

    included_ig: list[str] = []
    excl_ig: list[MetricExclusion] = []
    gains: list[float] = []
    for aid, chain in chains.items():
        defined = [
            c
            for c in chain.calibrations.values()
            if (c.get("prediction_presence") or {}).get("information_gain")
            and c.get("realized_information_gain") is not None
        ]
        if not defined:
            excl_ig.append(MetricExclusion(id=aid, reason="information_gain not defined"))
            continue
        included_ig.append(aid)
        gains.extend(float(c["realized_information_gain"]) for c in defined)
    information_gain = _slice(
        "assurance.information_gain.v1",
        numerator=float(sum(gains) / len(gains)) if gains else 0.0,
        population=action_ids,
        included=included_ig,
        exclusions=excl_ig,
    )

    included_cost: list[str] = []
    excl_cost: list[MetricExclusion] = []
    costs: list[float] = []
    for aid, chain in chains.items():
        defined = [
            c
            for c in chain.calibrations.values()
            if (c.get("prediction_presence") or {}).get("cost")
            and c.get("realized_cost") is not None
        ]
        if not defined:
            excl_cost.append(MetricExclusion(id=aid, reason="cost not defined"))
            continue
        included_cost.append(aid)
        costs.extend(float(c["realized_cost"]) for c in defined)
    cost = _slice(
        "assurance.cost.v1",
        numerator=float(sum(costs) / len(costs)) if costs else 0.0,
        population=action_ids,
        included=included_cost,
        exclusions=excl_cost,
    )

    included_m: list[str] = []
    excl_m: list[MetricExclusion] = []
    num_m = 0.0
    for aid, chain in chains.items():
        if not chain.outcomes and not chain.calibrations:
            excl_m.append(MetricExclusion(id=aid, reason="no outcome/calibration records"))
            continue
        included_m.append(aid)
        has_missing = any(
            (o.get("missing_data") or {}).get("has_missing_data") for o in chain.outcomes.values()
        ) or any(
            (c.get("missingness") or {}).get("has_missing_fields")
            for c in chain.calibrations.values()
        )
        if has_missing:
            num_m += 1.0
    missingness = _slice(
        "assurance.missingness.v1",
        numerator=num_m,
        population=action_ids,
        included=included_m,
        exclusions=excl_m,
    )

    included_rc: list[str] = []
    excl_rc: list[MetricExclusion] = []
    num_rc = 0.0
    for aid, chain in chains.items():
        included_rc.append(aid)
        gaps = list_gaps(chain)
        structural = [g for g in gaps if g["gap_id"].startswith("missing_node_class:")]
        if not structural:
            num_rc += 1.0
    reconstruction = _slice(
        "assurance.reconstruction_completeness.v1",
        numerator=num_rc,
        population=action_ids,
        included=included_rc,
        exclusions=excl_rc,
    )

    metrics = {
        "evidence_sufficiency": evidence_sufficiency.model_dump(mode="json"),
        "decision_and_review_agreement": decision_review.model_dump(mode="json"),
        "outcome_resolution": outcome_resolution.model_dump(mode="json"),
        "calibration_error": calibration_error.model_dump(mode="json"),
        "replication_rate": replication_rate.model_dump(mode="json"),
        "adverse_event_frequency": adverse.model_dump(mode="json"),
        "time_to_outcome": time_to_outcome.model_dump(mode="json"),
        "information_gain": information_gain.model_dump(mode="json"),
        "cost": cost.model_dump(mode="json"),
        "missingness": missingness.model_dump(mode="json"),
        "reconstruction_completeness": reconstruction.model_dump(mode="json"),
    }
    return {
        "schema_version": "v1",
        "generated_at": utc_now_iso(),
        "population_action_ids": action_ids,
        "metrics": metrics,
        "notes": (
            "Denominators are population sizes; included_ids + exclusions partition the population."
        ),
    }


def reconcile_metric_slice(slice_data: dict[str, Any], population_size: int) -> None:
    """Assert included_ids + exclusions partition the population (visible denominators)."""
    exclusions = slice_data.get("exclusions") or []
    included = slice_data.get("included_ids") or []
    denom = float(slice_data.get("denominator") or 0)
    definition_id = slice_data.get("definition_id")
    if population_size and abs(denom - float(population_size)) > 1e-9:
        raise AssuranceValidationError(
            f"Denominator {denom} != population {population_size} for {definition_id}"
        )
    excluded_ids = [e["id"] if isinstance(e, dict) else e.id for e in exclusions]
    if len(included) + len(excluded_ids) != population_size:
        raise AssuranceValidationError(
            f"{definition_id}: included({len(included)}) + excluded({len(excluded_ids)}) "
            f"!= population({population_size})"
        )
    if set(included) & set(excluded_ids):
        raise AssuranceValidationError(
            f"{definition_id}: included_ids overlap exclusions"
        )
