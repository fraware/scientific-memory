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
  guarantee_type?: string | null;
};

export type PcsVerificationResult = {
  verification_id?: string;
  id?: string;
  status?: string;
  verifier?: string;
  verifier_version?: string;
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

export type PcsCanonicalDigests = {
  claim_artifact: string;
  runtime_receipt: string;
  trace_certificate: string;
  evidence_bundle: string;
  signed_bundle: string;
};

export type PcsReleaseManifestView = {
  release_id?: string;
  release_candidate?: string;
  generated_at?: string;
  validation_profile?: string;
  release_status?: string;
  signature_or_digest?: string;
  manifest_hash?: string;
  manifest_path?: string;
  producer_repos?: Record<string, { repo: string; commit: string }>;
};

export type PcsReleaseChainValidationView = {
  validation_id?: string;
  release_id?: string;
  release_candidate?: string;
  validator?: string;
  validator_version?: string;
  checked_at?: string;
  status?: string;
  artifacts_checked?: number;
  checks?: {
    check_id?: string;
    description?: string;
    status?: string;
    details?: Record<string, unknown>;
  }[];
  failure_codes?: string[];
  signature_or_digest?: string;
};

export type PcsArtifactRegistryEntry = {
  name: string;
  artifact_type: string;
  producer: string;
  schema: string;
  status: string;
  source_repo: string;
  source_commit: string;
  hash: string;
  semantic_checks_performed: string[];
};

export type PcsArtifactDependencyEdge = {
  from: string;
  to: string;
  kind?: string;
};

export type PcsClaimReadModel = {
  schema_version: string;
  claim_id: string;
  claim: PcsClaimSection;
  assumption_set: PcsNamedArtifact & { assumptions?: PcsAssumption[] };
  runtime_receipt: PcsNamedArtifact;
  trace_certificate: PcsNamedArtifact;
  evidence_bundle?: PcsNamedArtifact;
  verification_result?: PcsVerificationResult | null;
  release_manifest?: PcsReleaseManifestView;
  release_chain_validation?: PcsReleaseChainValidationView;
  artifact_registry?: PcsArtifactRegistryEntry[];
  artifact_dependency_graph?: PcsArtifactDependencyEdge[];
  release_manifest_hash?: string;
  signed_bundle_hash?: string;
  artifact_hashes: PcsHashRow[];
  canonical_digests?: PcsCanonicalDigests;
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
