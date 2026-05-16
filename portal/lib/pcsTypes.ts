/** PCS portal read model (from pipeline pcs_import/artifact_normalizer). */

export type PcsGuaranteeTypes = Record<string, boolean>;

export type PcsClaimSection = {
  id: string;
  text: string;
  status: string;
  signature_or_digest: string;
  guarantee_types: PcsGuaranteeTypes;
};

export type PcsAssumption = {
  id: string;
  text: string;
  kind?: string;
  status?: string;
};

export type PcsNamedArtifact = {
  id: string;
  schema_version?: string;
  status?: string;
  signature_or_digest?: string;
  source_repo?: string;
  source_commit?: string;
  summary?: string;
  payload?: Record<string, unknown>;
  [key: string]: unknown;
};

export type PcsVerificationCheck = {
  id: string;
  name: string;
  outcome: string;
  detail?: string;
  guarantee_type?: string;
};

export type PcsVerificationResult = {
  status?: string;
  overall_outcome?: string;
  signature_or_digest?: string;
  source_repo?: string;
  source_commit?: string;
  checks?: PcsVerificationCheck[];
};

export type PcsHashRow = {
  name: string;
  digest: string;
  algorithm?: string;
  source_artifact?: string;
};

export type PcsClaimReadModel = {
  schema_version: string;
  claim_id: string;
  claim: PcsClaimSection;
  assumption_set: PcsNamedArtifact & { assumptions?: PcsAssumption[] };
  runtime_receipt: PcsNamedArtifact;
  trace_certificate: PcsNamedArtifact;
  verification_result?: PcsVerificationResult | null;
  artifact_hashes: PcsHashRow[];
  source_repositories: { source_repo: string; source_commit: string }[];
  reproduce_commands: string[];
  verify_commands: string[];
  limitations: string[];
  limitation_notice: string;
  bundle_signature_or_digest: string;
};

export type PcsPortalExport = {
  schema_version: string;
  claim_ids: string[];
  claims: Record<string, PcsClaimReadModel>;
};
