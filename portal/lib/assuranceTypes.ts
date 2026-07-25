export type EvidenceClass =
  | "formally_checked"
  | "certificate_checked"
  | "runtime_observed"
  | "empirically_measured"
  | "human_reviewed"
  | "unchecked_advisory";

export type AssuranceNode = {
  node_id: string;
  action_id: string;
  node_class: string;
  summary: string;
  created_at?: string;
  privacy?: string;
  evidence_classes?: EvidenceClass[];
  payload_ref?: string | null;
  pcs_claim_id?: string | null;
};

export type AssuranceEdge = {
  edge_id: string;
  from_node_id: string;
  to_node_id: string;
  relation: string;
};

export type AssuranceGap = {
  gap_id: string;
  reason: string;
};

export type AssuranceOutcomeReadModel = {
  outcome_id: string;
  action_id: string;
  measured_result?: Record<string, unknown>;
  delayed_result_status?: string;
  missing_data?: Record<string, unknown>;
  replication_status?: string;
  adverse_events?: unknown[];
  evidence_classes?: EvidenceClass[];
  reviewer_assessment?: Record<string, unknown>;
  non_claim?: string;
};

export type AssuranceCalibrationReadModel = {
  calibration_id: string;
  action_id: string;
  prediction_presence?: Record<string, boolean>;
  predicted_success?: number | null;
  calibration_class?: string;
  aggregation_eligibility?: boolean;
  missingness?: Record<string, unknown>;
  non_claim?: string;
};

export type AssuranceActionModel = {
  action_id: string;
  nodes: AssuranceNode[];
  edges: AssuranceEdge[];
  outcomes: AssuranceOutcomeReadModel[];
  calibrations: AssuranceCalibrationReadModel[];
  gaps: AssuranceGap[];
  chronology: Array<{
    node_id: string;
    node_class: string;
    created_at?: string;
    summary?: string;
    evidence_classes?: EvidenceClass[];
  }>;
};

export type AssurancePortalExport = {
  schema_version: string;
  generated_at?: string;
  include_internal?: boolean;
  action_ids: string[];
  actions: Record<string, AssuranceActionModel>;
};
