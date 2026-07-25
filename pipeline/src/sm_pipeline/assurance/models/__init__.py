"""Pydantic mirrors for assurance schemas."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator

EvidenceClass = Literal[
    "formally_checked",
    "certificate_checked",
    "runtime_observed",
    "empirically_measured",
    "human_reviewed",
    "unchecked_advisory",
]
PrivacyLevel = Literal["public", "internal", "redacted"]
LifecycleState = Literal[
    "draft",
    "admissible_for_import",
    "imported",
    "superseded",
    "rejected",
    "indeterminate",
]
ExternalSystemKind = Literal["vsa", "akta", "scope", "pf", "pcs", "execution", "other"]
NodeClass = Literal[
    "source",
    "evidence",
    "claim",
    "proposed_action",
    "admissibility_decision",
    "review",
    "grant",
    "runtime_action",
    "verification_result",
    "outcome",
    "replication",
    "calibration_update",
]
EdgeRelation = Literal[
    "supports",
    "proposes",
    "decides",
    "reviews",
    "grants",
    "executes",
    "verifies",
    "realizes",
    "replicates",
    "calibrates",
    "depends_on",
]
CalibrationClass = Literal[
    "well_calibrated",
    "overconfident",
    "underconfident",
    "misprioritized",
    "inadmissible_action",
    "indeterminate",
    "not_aggregable",
]
DelayedResultStatus = Literal["not_delayed", "delayed_unresolved", "delayed_resolved"]


class IntegrityEnvelope(BaseModel):
    content_digest: str
    writer_identity: str
    schema_version: Literal["v1"] = "v1"
    created_at: str


class ExternalArtifactRef(BaseModel):
    schema_version: Literal["v1"] = "v1"
    ref_id: str
    system_kind: ExternalSystemKind
    artifact_id: str
    artifact_version: str | None = None
    content_digest: str
    uri: str | None = None
    lifecycle: LifecycleState
    snapshot_path: str | None = None
    notes: str | None = None


class MissingDataField(BaseModel):
    field: str
    reason: str


class ScientificOutcomeRecord(BaseModel):
    schema_version: Literal["v1"] = "v1"
    outcome_id: str
    action_id: str
    scientific_question_id: str
    claim_ids: list[str]
    proposed_action_id: str
    external_refs: list[ExternalArtifactRef] = Field(default_factory=list)
    pcs_claim_ids: list[str] = Field(default_factory=list)
    intervention_performed: dict[str, Any]
    protocol: dict[str, Any]
    protocol_deviations: list[dict[str, Any]] = Field(default_factory=list)
    measured_result: dict[str, Any]
    data_commitments: dict[str, Any]
    uncertainty: dict[str, Any]
    adverse_events: list[dict[str, Any]] = Field(default_factory=list)
    missing_data: dict[str, Any]
    delayed_result_status: DelayedResultStatus
    reviewer_assessment: dict[str, Any]
    replication_status: str
    environment_context: dict[str, Any]
    integrity: IntegrityEnvelope
    privacy: PrivacyLevel = "public"
    evidence_classes: list[EvidenceClass]


class PredictionPresence(BaseModel):
    success: bool
    information_gain: bool
    cost: bool
    time: bool
    risk: bool


class ActionCalibrationRecord(BaseModel):
    schema_version: Literal["v1"] = "v1"
    calibration_id: str
    action_id: str
    decision_basis: dict[str, Any]
    prediction_presence: PredictionPresence
    predicted_success: float | None = None
    predicted_information_gain: float | None = None
    predicted_cost: float | None = None
    predicted_time: float | None = None
    predicted_risk: float | None = None
    realized_outcome_id: str | None = None
    calibration_class: CalibrationClass
    admissibility_error: bool | None = None
    prioritization_error: bool | None = None
    authorization_error: bool | None = None
    verifier_disagreement: dict[str, Any]
    uncertainty: dict[str, Any]
    missingness: dict[str, Any]
    aggregation_eligibility: bool
    realized_success: bool | None = None
    realized_information_gain: float | None = None
    realized_cost: float | None = None
    realized_time: float | None = None
    integrity: IntegrityEnvelope
    privacy: PrivacyLevel = "public"

    @model_validator(mode="after")
    def _check_presence_and_aggregation(self) -> ActionCalibrationRecord:
        presence = self.prediction_presence
        pairs = [
            (presence.success, self.predicted_success, "predicted_success"),
            (presence.information_gain, self.predicted_information_gain, "predicted_information_gain"),
            (presence.cost, self.predicted_cost, "predicted_cost"),
            (presence.time, self.predicted_time, "predicted_time"),
            (presence.risk, self.predicted_risk, "predicted_risk"),
        ]
        for present, value, name in pairs:
            if present and value is None:
                raise ValueError(f"{name} required when prediction_presence flag is true")
            if not present and value is not None:
                raise ValueError(f"{name} must be null when prediction_presence flag is false")

        if self.aggregation_eligibility:
            if not self.realized_outcome_id:
                raise ValueError(
                    "aggregation_eligibility=true requires realized_outcome_id"
                )
        return self


class ActionChainNode(BaseModel):
    schema_version: Literal["v1"] = "v1"
    node_id: str
    action_id: str
    node_class: NodeClass
    summary: str
    created_at: str
    content_digest: str
    privacy: PrivacyLevel = "public"
    evidence_classes: list[EvidenceClass] = Field(default_factory=list)
    payload_ref: str | None = None
    pcs_claim_id: str | None = None
    external_ref_ids: list[str] = Field(default_factory=list)
    payload: dict[str, Any] | None = None


class ActionChainEdge(BaseModel):
    schema_version: Literal["v1"] = "v1"
    edge_id: str
    action_id: str
    from_node_id: str
    to_node_id: str
    relation: EdgeRelation
    created_at: str
    content_digest: str
    notes: str | None = None


class PathDigest(BaseModel):
    path: str
    digest: str


class ClaimPointer(BaseModel):
    claim_id: str
    digest: str


class PcsArtifacts(BaseModel):
    mode: Literal["bundle", "claim_pointers", "none"]
    bundle_path: str | None = None
    claim_pointers: list[ClaimPointer] = Field(default_factory=list)


class ReleaseArtifacts(BaseModel):
    refs: list[PathDigest] = Field(default_factory=list)
    pcs: PcsArtifacts
    execution: list[PathDigest] = Field(default_factory=list)
    outcomes: list[PathDigest] = Field(default_factory=list)
    calibrations: list[PathDigest] = Field(default_factory=list)
    nodes: list[PathDigest] = Field(default_factory=list)
    edges: list[PathDigest] = Field(default_factory=list)


class AssuranceReleaseManifest(BaseModel):
    schema_version: Literal["v1"] = "v1"
    release_id: str
    action_id: str
    created_at: str
    lifecycle: LifecycleState
    producer: str | None = None
    artifacts: ReleaseArtifacts
    checksums_path: Literal["checksums.txt"] = "checksums.txt"
    notes: str | None = None


class MetricExclusion(BaseModel):
    id: str
    reason: str


class MetricSlice(BaseModel):
    definition_id: str
    numerator: float
    denominator: float
    included_ids: list[str] = Field(default_factory=list)
    exclusions: list[MetricExclusion] = Field(default_factory=list)
    notes: str | None = None


class AutonomousScienceMetrics(BaseModel):
    schema_version: Literal["v1"] = "v1"
    generated_at: str
    population_action_ids: list[str]
    metrics: dict[str, MetricSlice]
    notes: str | None = None


def utc_now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
