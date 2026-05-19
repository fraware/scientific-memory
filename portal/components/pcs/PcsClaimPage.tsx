import type { PcsClaimReadModel } from "@/lib/pcsTypes";

import { ArtifactDependencyGraph } from "./ArtifactDependencyGraph";
import { HandoffManifestView } from "./HandoffManifestView";
import { ArtifactHashTable } from "./ArtifactHashTable";
import { ArtifactRegistryView } from "./ArtifactRegistryView";
import { AssumptionSetView } from "./AssumptionSetView";
import { ClaimArtifactView } from "./ClaimArtifactView";
import { EvidenceBundleView } from "./EvidenceBundleView";
import { LimitationNotice } from "./LimitationNotice";
import { LineageView } from "./LineageView";
import { ProtocolArtifactsSection } from "./ProtocolArtifactsSection";
import { WorkflowProfileView } from "./WorkflowProfileView";
import { ReleaseChainValidationView } from "./ReleaseChainValidationView";
import { ReleaseManifestView } from "./ReleaseManifestView";
import { StalenessView } from "./StalenessView";
import { ReplayCommand } from "./ReplayCommand";
import { RuntimeReceiptView } from "./RuntimeReceiptView";
import { SourceRepositories } from "./SourceRepositories";
import { ComputationRunReceiptView } from "./ComputationRunReceiptView";
import { ComputationWitnessView } from "./ComputationWitnessView";
import { DatasetReceiptView } from "./DatasetReceiptView";
import { EnvironmentReceiptView } from "./EnvironmentReceiptView";
import { ResultArtifactView } from "./ResultArtifactView";
import { ToolUseCertificateView } from "./ToolUseCertificateView";
import { ToolUseTraceView } from "./ToolUseTraceView";
import { TraceCertificateView } from "./TraceCertificateView";
import { VerificationResultView } from "./VerificationResultView";

interface PcsClaimPageProps {
  model: PcsClaimReadModel;
}

export function PcsClaimPage({ model }: PcsClaimPageProps) {
  const extraLimitations = model.limitations.filter(
    (l) => l !== model.limitation_notice,
  );
  const domainLabel = model.domain ?? model.workflow_profile?.domain;
  const hasTemporalCertificate =
    Boolean(model.trace_certificate?.id) &&
    model.certificate_artifact_types?.includes("TraceCertificate.v0");
  const isComputationDomain =
    model.domain === "scientific_computation" ||
    model.workflow_id === "scientific_computation.reproducibility_v0";

  return (
    <main className="mx-auto max-w-5xl space-y-8 p-8" data-testid="pcs-claim-page">
      <header>
        <p className="text-sm text-gray-500">
          {domainLabel ? `PCS release · ${domainLabel}` : "PCS scientific release"}
        </p>
        <h1 className="text-3xl font-semibold">{model.claim_id}</h1>
        {model.workflow_id ? (
          <p className="mt-1 font-mono text-xs text-gray-500">
            Workflow: {model.workflow_id}
          </p>
        ) : null}
        <p className="mt-1 font-mono text-xs text-gray-500">
          Bundle digest: {model.bundle_signature_or_digest}
        </p>
      </header>

      <ClaimArtifactView claim={model.claim} />
      {model.workflow_profile ? (
        <WorkflowProfileView profile={model.workflow_profile} />
      ) : null}
      <AssumptionSetView assumptionSet={model.assumption_set} />
      {!isComputationDomain ? <RuntimeReceiptView receipt={model.runtime_receipt} /> : null}
      {model.dataset_receipt ? <DatasetReceiptView receipt={model.dataset_receipt} /> : null}
      {model.environment_receipt ? (
        <EnvironmentReceiptView receipt={model.environment_receipt} />
      ) : null}
      {model.computation_run_receipt ? (
        <ComputationRunReceiptView receipt={model.computation_run_receipt} />
      ) : null}
      {model.result_artifact ? <ResultArtifactView artifact={model.result_artifact} /> : null}
      {model.computation_witness ? (
        <ComputationWitnessView witness={model.computation_witness} />
      ) : null}
      {model.tool_use_trace ? <ToolUseTraceView trace={model.tool_use_trace} /> : null}
      {model.tool_use_certificate ? (
        <ToolUseCertificateView certificate={model.tool_use_certificate} />
      ) : null}
      {hasTemporalCertificate ? (
        <TraceCertificateView certificate={model.trace_certificate} />
      ) : null}
      {model.evidence_bundle?.id ? (
        <EvidenceBundleView evidence={model.evidence_bundle} />
      ) : null}
      <VerificationResultView result={model.verification_result} />
      {model.release_manifest ? (
        <ReleaseManifestView manifest={model.release_manifest} />
      ) : null}
      {model.release_chain_validation ? (
        <ReleaseChainValidationView validation={model.release_chain_validation} />
      ) : null}
      {model.artifact_registry?.length ? (
        <ArtifactRegistryView entries={model.artifact_registry} />
      ) : null}
      {model.handoff_manifests?.length ? (
        <HandoffManifestView handoffs={model.handoff_manifests} />
      ) : null}
      {model.protocol_artifacts?.length ? (
        <ProtocolArtifactsSection artifacts={model.protocol_artifacts} />
      ) : null}
      {model.artifact_dependency_graph?.length ? (
        <ArtifactDependencyGraph edges={model.artifact_dependency_graph} />
      ) : null}
      {model.lineage ? <LineageView lineage={model.lineage} /> : null}
      {model.staleness ? <StalenessView staleness={model.staleness} /> : null}
      <ArtifactHashTable
        hashes={model.artifact_hashes}
        canonicalDigests={model.canonical_digests}
      />
      <SourceRepositories sources={model.source_repositories} />
      <ReplayCommand
        reproduceCommands={model.reproduce_commands}
        verifyCommands={model.verify_commands}
      />
      <LimitationNotice notice={model.limitation_notice} additional={extraLimitations} />
    </main>
  );
}
